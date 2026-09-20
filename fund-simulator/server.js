const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const axios = require('axios');
const cheerio = require('cheerio');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const history = require('connect-history-api-fallback');
const orderEngine = require('./engine/order-engine');
const { confirmPendingOrders } = orderEngine;
const feeEngine = require('./engine/fee');
const FundDataFetcher = require('./data-fetcher');

const app = express();
// 模块化：时间/交易日纯函数、AI 事件总线、统一错误处理（见 CODING_STANDARDS.md）
const { getLocalDateStr, isTradingDay, isMarketOpenNow, nextTradingDay } = require('./utils/time');
const { aiBus, logAi, init: initAiBus } = require('./events/aiBus');
const { errorHandler, asyncHandler } = require('./middleware/errorHandler');
const PORT = process.env.PORT || 3000;

// 中间件
app.use(express.json());
// 注意：静态文件服务放在API路由之后，避免拦截API请求

// 基金/组合 API 路由（与 server-production.js 共用，保证 /api/funds 等可用）
app.use('/api', require('./api/routes'));

// 数据文件路径
const DATA_FILE = path.join(__dirname, 'data', 'ai_data.json');

// 确保数据目录存在
const dataDir = path.join(__dirname, 'data');
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

// 数据库初始化
const db = new sqlite3.Database('./fund_simulator.db', (err) => {
  if (err) {
    console.error('数据库连接失败:', err.message);
  } else {
    console.log('已连接到SQLite数据库');
    initAiBus(db); // AI 事件总线绑定 db，logAi 才能落档
    initDatabase();
  }
});

// 初始化数据库表（幂等：不删除已有数据，仅确保表存在）
function initDatabase() {
  db.serialize(() => {
    // 基金信息表
    db.run(`CREATE TABLE IF NOT EXISTS funds (
      fund_code TEXT PRIMARY KEY,
      fund_name TEXT NOT NULL,
      fund_type TEXT,
      inception_date TEXT,
      benchmark TEXT,
      manager TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);

    // 基金净值表
    db.run(`CREATE TABLE IF NOT EXISTS fund_nav (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      fund_code TEXT NOT NULL,
      nav_date TEXT NOT NULL,
      unit_nav REAL,
      acc_nav REAL,
      daily_return REAL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (fund_code) REFERENCES funds (fund_code),
      UNIQUE(fund_code, nav_date)
    )`);

    // 交易记录表（持久化）
    db.run(`CREATE TABLE IF NOT EXISTS transactions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      fund_code TEXT NOT NULL,
      transaction_type TEXT NOT NULL,
      amount REAL NOT NULL,
      price REAL NOT NULL,
      shares REAL NOT NULL,
      fees REAL DEFAULT 0,
      transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
      reason TEXT,
      FOREIGN KEY (fund_code) REFERENCES funds (fund_code)
    )`);

    // 持仓表（持久化）
    db.run(`CREATE TABLE IF NOT EXISTS holdings (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      fund_code TEXT NOT NULL,
      shares REAL DEFAULT 0,
      cost_price REAL,
      total_cost REAL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(user_id, fund_code)
    )`);

    // 用户配置表
    db.run(`CREATE TABLE IF NOT EXISTS user_configs (
      user_id TEXT PRIMARY KEY,
      config TEXT NOT NULL,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);

    // 已实现盈亏账本（卖出确认时记录 netProceeds - 卖出成本；正=盈利，负=亏损+赎回费）
    db.run(`CREATE TABLE IF NOT EXISTS realized_pnl (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      fund_code TEXT NOT NULL,
      amount REAL NOT NULL,
      sell_fee REAL DEFAULT 0,
      note TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);

    // 自选观察池表
    db.run(`CREATE TABLE IF NOT EXISTS watchlist (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      fund_code TEXT NOT NULL,
      reason TEXT,
      source TEXT DEFAULT 'manual',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(user_id, fund_code),
      FOREIGN KEY (fund_code) REFERENCES funds (fund_code)
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS holidays (
      date TEXT PRIMARY KEY,
      name TEXT
    )`);
    // seed 2026 年休市日（幂等）
    const hd = (require('./engine/holidays.json')['2026'] || []);
    const hStmt = db.prepare('INSERT OR IGNORE INTO holidays (date, name) VALUES (?, ?)');
    hd.forEach(d => hStmt.run(d, '法定节假日休市'));
    hStmt.finalize();

    // 幂等迁移：老库 watchlist 无 source 列时补列（默认 manual）
    // 迁移完成后再执行初始观察名单迁移（seedWatchlist 依赖 source 列存在）
    db.all('PRAGMA table_info(watchlist)', (pragmaErr, cols) => {
      const hasSource = !pragmaErr && (cols || []).some(c => c.name === 'source');
      if (hasSource) {
        seedWatchlist();
      } else {
        db.run('ALTER TABLE watchlist ADD COLUMN source TEXT DEFAULT \'manual\'', (altErr) => {
          if (altErr) console.error('watchlist 补 source 列失败:', altErr.message);
          else console.log('watchlist 已补充 source 列');
          seedWatchlist();
        });
      }
    });

    // 每日账户快照表（资产走势/每日盈亏图的数据源，收盘时写入）
    db.run(`CREATE TABLE IF NOT EXISTS portfolio_daily (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      date TEXT NOT NULL,
      total_assets REAL,
      daily_pnl REAL,
      cash REAL,
      market_value REAL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(user_id, date)
    )`);

    // 将内置用户配置中的观察名单迁入 watchlist 表（幂等，在 source 列迁移完成后执行）
    // P0-1 订单引擎相关表（规格: AI_FUND_OPERATIONS_DESIGN.md §5.2）
    db.run(`CREATE TABLE IF NOT EXISTS orders (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      fund_code TEXT NOT NULL,
      order_type TEXT NOT NULL,
      amount REAL NOT NULL,
      shares REAL DEFAULT 0,
      price REAL NOT NULL,
      fee REAL DEFAULT 0,
      status TEXT DEFAULT 'SUBMITTED',
      order_date TEXT,
      trade_date TEXT,
      confirm_date TEXT,
      reason TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);

    // 旧库迁移：orders.trade_date（T 日确认净值日；历史订单默认等于下单日，行为不变）
    db.run(`ALTER TABLE orders ADD COLUMN trade_date TEXT`, (err) => {
      if (!err) {
        db.run(`UPDATE orders SET trade_date = order_date WHERE trade_date IS NULL OR trade_date = ''`, (e) => {
          if (e) console.error('orders.trade_date 回填失败:', e.message);
        });
      }
    });

    db.run(`CREATE TABLE IF NOT EXISTS fund_fees (
      fund_code TEXT PRIMARY KEY,
      buy_fee_pct REAL, sell_fee_7d REAL, sell_fee_1y REAL, sell_fee_ge1y REAL,
      manage_fee_pct REAL, custody_fee_pct REAL, service_fee_pct REAL,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);
    db.run(`CREATE TABLE IF NOT EXISTS audit_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      actor TEXT,
      action TEXT,
      target TEXT,
      detail TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);
    db.run(`CREATE TABLE IF NOT EXISTS ai_event_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      event_type TEXT,
      user_name TEXT,
      message TEXT,
      detail TEXT,
      event_time DATETIME
    )`)
    db.run(`CREATE TABLE IF NOT EXISTS scheduler_runs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      run_type TEXT,
      started_at DATETIME,
      finished_at DATETIME,
      status TEXT,
      summary TEXT
    )`);
    db.run(`CREATE TABLE IF NOT EXISTS risk_params (
      user_id TEXT NOT NULL,
      param_name TEXT NOT NULL,
      param_value TEXT,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(user_id, param_name)
    )`);
    db.run(`CREATE TABLE IF NOT EXISTS risk_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      event_type TEXT,
      fund_code TEXT,
      detail TEXT,
      action TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);
    db.run(`CREATE TABLE IF NOT EXISTS performance_daily (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      date TEXT NOT NULL,
      total_return REAL,
      benchmark_return REAL,
      excess_return REAL,
      volatility REAL,
      sharpe REAL,
      max_drawdown REAL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(user_id, date)
    )`);
    db.run(`CREATE TABLE IF NOT EXISTS reports (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      report_type TEXT,
      period TEXT,
      content TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);
    db.run(`CREATE TABLE IF NOT EXISTS fund_profiles (
      fund_code TEXT PRIMARY KEY,
      volatility REAL,
      downside_risk REAL,
      style_label TEXT,
      score REAL,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);
    db.run(`CREATE TABLE IF NOT EXISTS dividends (
      fund_code TEXT NOT NULL,
      ex_date TEXT NOT NULL,
      per_unit REAL,
      type TEXT DEFAULT 'CASH',
      nav_before REAL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(fund_code, ex_date)
    )`);
    db.run(`CREATE TABLE IF NOT EXISTS data_quality_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      fund_code TEXT,
      nav_date TEXT,
      issue_type TEXT,
      detail TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);
    db.run(`CREATE TABLE IF NOT EXISTS market_env (
      date TEXT PRIMARY KEY,
      avg_fund_chg REAL,
      bench_chg REAL,
      temperature TEXT,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);
    db.run(`CREATE TABLE IF NOT EXISTS benchmark_daily (
      date TEXT PRIMARY KEY,
      value REAL,
      change_pct REAL,
      source TEXT DEFAULT 'eastmoney'
    )`);
    db.run(`CREATE TABLE IF NOT EXISTS research_notes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      fund_code TEXT NOT NULL,
      analysis_type TEXT,
      signal TEXT,
      reason TEXT,
      metrics TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);

    // seedWatchlist();

    // AI分析结果表
    db.run(`CREATE TABLE IF NOT EXISTS ai_analysis (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      fund_code TEXT NOT NULL,
      decision TEXT,
      confidence TEXT,
      entry_price REAL,
      target_price REAL,
      stop_loss REAL,
      analysis_time DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (fund_code) REFERENCES funds (fund_code)
    )`);

    console.log('数据库表初始化完成');
    
    // 初始化用户数据
    initializeUserData();
  });
}

// 用户配置
const userConfigs = {
  'default': {
    id: 'default',
    name: '默认用户',
    avatar: '👤',
    style: '稳健型',
    description: '稳健投资，追求长期稳定收益',
    initial_capital: 100000,
    risk_tolerance: 'medium',
    target_return: 0.10,
    // ==== 性格画像（AI_FUND_OPERATIONS_DESIGN.md §2.2，决策/风控/退场全部由此派生）====
    stop_loss: 0.05,             // 单基金止损线（-5%）
    take_profit: 0.20,           // 单基金止盈线（+20%）
    max_position: 0.60,          // 总仓位上限 60%
    max_single_fund: 0.20,       // 单基金仓位上限 20%
    min_hold_funds: 3,           // 最少持仓基金数（分散要求）
    max_drawdown: 0.10,          // 组合回撤熔断线（-10%）
    exit_drawdown: 15,           // 单基金距60日高点回撤超 15% 触发减仓评估
    exit_style: 'timely',        // 退场风格：及时（触发即减/清）
    entry_signal_threshold: 'strong', // 入场门槛：仅 buy 强信号
    buy_ratio: 0.2, add_ratio: 0.1,  // 建仓/加仓比例
    add_cooldown_days: 5,        // 分批加仓冷却期（天）：距上次确认买入满 N 天才可再加仓
    rebalance_frequency: 'monthly',  // 再平衡频率
    watchlist_style: '均衡分散/大盘蓝筹', // 选基偏好
    base_weights: { '混合型': 0.5, '股票型': 0.3, '指数型': 0.2 }, // 目标资产配置
    fund_list: ['110011', '161725', '003834', '005827', '005267'],
    watchlist: [
      { code: '000001', name: '华夏成长混合', type: '混合型', reason: '基金经理优秀，长期看好' },
      { code: '000011', name: '华夏大盘精选', type: '混合型', reason: '历史业绩突出' },
      { code: '000041', name: '华夏全球股票', type: '股票型', reason: '分散投资，全球配置' }
    ]
  },
  'aggressive': {
    id: 'aggressive',
    name: '激进用户',
    avatar: '🚀',
    style: '激进型',
    description: '追求高收益，愿意承担更高风险',
    initial_capital: 100000,
    risk_tolerance: 'high',
    target_return: 0.20,
    // ==== 性格画像（激进：更高容忍、更晚退场）====
    stop_loss: 0.10,             // 止损线 -10%
    take_profit: 0.40,           // 止盈线 +40%
    max_position: 1.00,          // 总仓位上限 100%
    max_single_fund: 0.40,       // 单基金上限 40%
    min_hold_funds: 2,
    max_drawdown: 0.20,          // 回撤熔断 -20%
    exit_drawdown: 25,           // 单基金回撤 25% 才评估
    exit_style: 'patient',       // 退场风格：容忍（恶化确认 2 日才减）
    entry_signal_threshold: 'medium', // 入场门槛：buy/add 都买
    buy_ratio: 0.2, add_ratio: 0.1,
    add_cooldown_days: 3,        // 分批加仓冷却期（天）：激进用户加仓节奏更快
    rebalance_frequency: 'weekly',
    watchlist_style: '成长/主题/高弹性',
    base_weights: { '混合型': 0.4, '股票型': 0.5, '指数型': 0.1 },
    fund_list: ['003834', '001156', '001938', '320007', '260108'],
    watchlist: [
      { code: '001015', name: '华夏沪深300指数增强', type: '指数型', reason: '高弹性，反弹空间大' },
      { code: '002001', name: '华夏回报混合', type: '混合型', reason: '攻守兼备' },
      { code: '002011', name: '华夏红利混合', type: '混合型', reason: '高股息策略' }
    ]
  }
};

// 当前活跃用户（拆 routes 时用 getter/setter 保持引用）
let currentUser = 'default';
const getCurrentUser = () => currentUser;
const setCurrentUser = (v) => { currentUser = v; };

// 初始化用户数据（从数据库加载）
function initializeUserData() {
  // 检查是否有历史交易记录
  db.get('SELECT COUNT(*) as count FROM transactions WHERE user_id = ?', ['default'], (err, row) => {
    if (err) {
      console.error('检查交易记录失败:', err);
      return;
    }
    
    console.log(`默认用户交易记录数: ${row.count}`);
    
    if (row.count > 0) {
      console.log('检测到历史交易记录，加载中...');
    } else {
      console.log('无历史交易记录，首次运行');
    }
  });
}

// 将内置用户配置中的观察名单迁入 watchlist 表（幂等，仅补充缺失项）
function seedWatchlist() {
  for (const [userId, user] of Object.entries(userConfigs)) {
    if (!user.watchlist || user.watchlist.length === 0) continue;
    const stmt = db.prepare('INSERT OR IGNORE INTO watchlist (user_id, fund_code, reason, source) VALUES (?, ?, ?, \'manual\')');
    user.watchlist.forEach(item => {
      stmt.run(userId, item.code, item.reason || '');
    });
    stmt.finalize();
  }
  console.log('观察池初始名单已就绪');
}

// 查询用户观察池（附带基金真实信息、最新净值与走势信号）
function getWatchlist(userId) {
  return new Promise((resolve, reject) => {
    const sql = `
      SELECT w.fund_code, w.reason, w.source,
             f.fund_name, f.fund_type,
             (SELECT unit_nav FROM fund_nav WHERE fund_code = w.fund_code ORDER BY nav_date DESC LIMIT 1) AS latest_nav,
             (SELECT daily_return FROM fund_nav WHERE fund_code = w.fund_code ORDER BY nav_date DESC LIMIT 1) AS daily_return,
             (SELECT nav_date FROM fund_nav WHERE fund_code = w.fund_code ORDER BY nav_date DESC LIMIT 1) AS nav_date,
             (SELECT unit_nav FROM fund_nav WHERE fund_code = w.fund_code ORDER BY nav_date DESC LIMIT 1 OFFSET 5) AS nav_5d_ago,
             (SELECT unit_nav FROM fund_nav WHERE fund_code = w.fund_code ORDER BY nav_date DESC LIMIT 1 OFFSET 20) AS nav_20d_ago,
             (SELECT MAX(unit_nav) FROM (SELECT unit_nav FROM fund_nav WHERE fund_code = w.fund_code ORDER BY nav_date DESC LIMIT 60)) AS high_60d,
             (SELECT AVG(unit_nav) FROM (SELECT unit_nav FROM fund_nav WHERE fund_code = w.fund_code ORDER BY nav_date DESC LIMIT 20)) AS ma20
      FROM watchlist w
      LEFT JOIN funds f ON w.fund_code = f.fund_code
      WHERE w.user_id = ?
      ORDER BY w.created_at DESC, w.id DESC
    `;
    db.all(sql, [userId], (err, rows) => {
      if (err) reject(err);
      else resolve((rows || []).map(row => {
        const signal = buildWatchSignal(row);
        return {
          fund_code: row.fund_code,
          fund_name: row.fund_name,
          fund_type: row.fund_type,
          reason: row.reason || '',
          source: row.source || 'manual',
          latest_nav: row.latest_nav,
          daily_return: row.daily_return,
          nav_date: row.nav_date,
          change_5d: row.change_5d,
          change_20d: row.change_20d,
          drawdown_60d: row.drawdown_60d,
          above_ma20: row.above_ma20,
          signal
        };
      }));
    });
  });
}

// 基于真实净值计算观察信号：趋势 + 回撤 + 均线位置
function buildWatchSignal(row) {
  const latest = row.latest_nav;
  if (latest == null || latest <= 0) {
    return { action: 'wait', label: '数据不足', reason: '暂无足够净值数据，暂无法分析' };
  }
  const change5 = row.nav_5d_ago != null && row.nav_5d_ago > 0 ? ((latest / row.nav_5d_ago - 1) * 100) : null;
  const change20 = row.nav_20d_ago != null && row.nav_20d_ago > 0 ? ((latest / row.nav_20d_ago - 1) * 100) : null;
  const dd = row.high_60d != null && row.high_60d > 0 ? ((latest / row.high_60d - 1) * 100) : null;
  const aboveMa20 = row.ma20 != null && row.ma20 > 0 ? latest >= row.ma20 : null;

  row.change_5d = change5 != null ? Number(change5.toFixed(2)) : null;
  row.change_20d = change20 != null ? Number(change20.toFixed(2)) : null;
  row.drawdown_60d = dd != null ? Number(dd.toFixed(2)) : null;
  row.above_ma20 = aboveMa20;

  // 信号规则：中期趋势（20日）为主，结合回撤深度与均线位置
  const trendUp = change20 != null && change20 >= 0;
  const ddAbs = dd != null ? Math.abs(dd) : null;

  if (trendUp) {
    if (ddAbs != null && ddAbs >= 8 && aboveMa20) {
      return { action: 'buy', label: '分批建仓', reason: `中期趋势向上（近20日 +${change20.toFixed(1)}%），自60日高点回调 ${ddAbs.toFixed(1)}% 且已站上20日线，回调企稳，可分批入场` };
    }
    if (ddAbs != null && ddAbs >= 3) {
      return { action: 'add', label: '逢低加仓', reason: `中期趋势向上（近20日 +${change20.toFixed(1)}%），当前距60日高点回调 ${ddAbs.toFixed(1)}%，处于相对低位，可逢低分批加仓` };
    }
    return { action: 'watch', label: '回踩再入', reason: `中期趋势向上（近20日 +${change20.toFixed(1)}%），但已接近60日高点（回撤仅 ${ddAbs != null ? ddAbs.toFixed(1) : '0.0'}%），追高风险较大，建议等回踩再入场` };
  }
  // 中期趋势向下
  if (aboveMa20) {
    return { action: 'add', label: '轻仓试探', reason: `中期趋势偏弱（近20日 ${change20 != null ? change20.toFixed(1) : '—'}%），但已站上20日线，或现底部反弹，可轻仓试探` };
  }
  return { action: 'wait', label: '暂缓入场', reason: `中期趋势向下（近20日 ${change20 != null ? change20.toFixed(1) : '—'}%），且处于20日线下方，尚未企稳，建议观望等信号` };
}

// 获取用户观察池代码列表（观察池 = AI 选股池）
// 审计日志（全链路留痕）
function audit(actor, action, target, params) {
  let detail = '';
  try { detail = JSON.stringify(params || {}); } catch (e) {}
  db.run(`INSERT INTO audit_logs (actor, action, target, detail) VALUES (?, ?, ?, ?)`,
    [actor, action, String(target || ''), detail], (err) => {
      if (err) console.error('审计日志写入失败:', err.message);
    });
}

// ============ P0-2 退场信号 + 风控引擎（规格 §2.2/§4.3/§4.5）============

// 读取用户风控参数（risk_params 表可覆盖 userConfigs 默认）
function getRiskParams(userId) {
  return new Promise((resolve) => {
    const base = userConfigs[userId] || {};
    db.all('SELECT param_name, param_value FROM risk_params WHERE user_id = ?', [userId], (err, rows) => {
      if (err || !rows || rows.length === 0) return resolve(base);
      const merged = { ...base };
      rows.forEach(r => { merged[r.param_name] = isNaN(Number(r.param_value)) ? r.param_value : Number(r.param_value); });
      resolve(merged);
    });
  });
}

// 连续下跌天数（近 N 个交易日 daily_return < 0 的连续计数）
function getConsecutiveDownDays(fundCode) {
  return new Promise((resolve) => {
    db.all('SELECT nav_date, daily_return FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 10', [fundCode], (err, rows) => {
      if (err || !rows) return resolve(0);
      let n = 0;
      for (const r of rows) {
        if (r.daily_return != null && r.daily_return < 0) n++;
        else break;
      }
      resolve(n);
    });
  });
}

// 持仓退场信号引擎：止损/止盈/趋势转空/回撤过大/连跌，按性格输出 sell/reduce/hold
async function buildExitSignal(userId, fundCode, holding, userCfg) {
  const sig = await getFundSignal(fundCode);
  if (!sig || sig.latest_nav == null || sig.latest_nav <= 0) {
    return { action: 'hold', label: '数据不足', reason: '暂无净值数据，暂维持持有' };
  }
  const nav = sig.latest_nav;
  const cost = holding.cost || holding.cost_price || 0;
  const pnlPct = cost > 0 ? (nav / cost - 1) * 100 : 0;
  const stopLossPct = (userCfg.stop_loss || 0.05) * 100;
  const takeProfitPct = (userCfg.take_profit || 0.25) * 100;
  const exitDrawdown = userCfg.exit_drawdown || 15;
  const exitStyle = userCfg.exit_style || 'timely';
  const name = userCfg.name || userId;
  const consecDown = await getConsecutiveDownDays(fundCode);

  // 1) 止损：亏损达止损线
  if (pnlPct <= -stopLossPct) {
    if (exitStyle === 'patient' && consecDown < 2) {
      return { action: 'reduce', label: '减仓止损', ratio: 0.5,
        reason: `亏损 ${pnlPct.toFixed(1)}% 触及止损线（-${stopLossPct}%），${name}为激进风格，连续下跌 ${consecDown} 日未确认恶化，先减 50% 控险` };
    }
    return { action: 'sell', label: '清仓止损', ratio: 1,
      reason: `亏损 ${pnlPct.toFixed(1)}% 触发止损线（-${stopLossPct}%），${name}按 ${exitStyle === 'timely' ? '及时' : '恶化确认'} 风格执行` };
  }
  // 2) 止盈：盈利达止盈线
  if (pnlPct >= takeProfitPct) {
    if (exitStyle === 'timely') {
      return { action: 'reduce', label: '止盈减仓', ratio: 0.5,
        reason: `盈利 ${pnlPct.toFixed(1)}% 达止盈线（+${takeProfitPct}%），稳健风格锁定一半利润` };
    }
    return { action: 'hold', label: '持有奔跑',
      reason: `盈利 ${pnlPct.toFixed(1)}% 达止盈线，${name}为激进风格，继续持有等趋势转空` };
  }
  // 3) 趋势转空：近20日下跌 且 跌破20日线
  if (sig.change_20d != null && sig.change_20d < 0 && sig.above_ma20 === false) {
    if (exitStyle === 'patient' && consecDown < 2) {
      return { action: 'hold', label: '观察确认',
        reason: `近20日 ${sig.change_20d.toFixed(1)}% 且跌破20日线，激进风格等待连续恶化确认` };
    }
    return { action: 'reduce', label: '趋势转空减仓', ratio: 0.5,
      reason: `近20日 ${sig.change_20d.toFixed(1)}% 且跌破20日线，趋势转空，减仓 50%` };
  }
  // 4) 单基金回撤过大（距60日高点）
  if (sig.drawdown_60d != null && sig.drawdown_60d >= exitDrawdown) {
    return { action: 'reduce', label: '回撤过大减仓', ratio: 0.5,
      reason: `距60日高点回撤 ${sig.drawdown_60d.toFixed(1)}% 超 ${exitDrawdown}% 阈值，减仓控制风险` };
  }
  return { action: 'hold', label: '继续持有', reason: '未触发退场条件' };
}

// 组合当前回撤（基于 portfolio_daily 快照峰值，P0-3 完善为波动窗口）
function getPortfolioDrawdown(userId) {
  return new Promise((resolve) => {
    db.all('SELECT date, total_assets FROM portfolio_daily WHERE user_id = ? ORDER BY date', [userId], (err, rows) => {
      if (err || !rows || rows.length < 2) return resolve(null);
      let peak = rows[0].total_assets;
      let maxDD = 0;
      for (const r of rows) {
        if (r.total_assets > peak) peak = r.total_assets;
        if (peak > 0) maxDD = Math.max(maxDD, (peak - r.total_assets) / peak * 100);
      }
      resolve(maxDD);
    });
  });
}

// 风控校验（下单前）：回撤熔断 / 单基金集中度 / 总仓位
async function checkRiskControls(userId, portfolio, orderType, fundCode, amount, userCfg) {
  const totalAssets = portfolio.current_capital + Object.values(portfolio.holdings).reduce((sum, h) => sum + (h.total_cost || 0), 0);
  if (orderType === 'BUY') {
    const dd = await getPortfolioDrawdown(userId);
    const maxDD = (userCfg.max_drawdown || 0.15) * 100;
    if (dd != null && dd >= maxDD) {
      return { pass: false, reason: `组合回撤 ${dd.toFixed(1)}% 达熔断线（-${maxDD}%），暂停新买入，仅允许减仓` };
    }
    const maxSingle = (userCfg.max_single_fund || 0.2) * totalAssets;
    const curHoldingVal = portfolio.holdings[fundCode] ? (portfolio.holdings[fundCode].total_cost || 0) : 0;
    if (curHoldingVal + amount > maxSingle) {
      return { pass: false, reason: `单基金仓位将超上限（≤${(userCfg.max_single_fund * 100).toFixed(0)}%），当前+拟买超限` };
    }
    const maxPos = (userCfg.max_position || 0.3) * totalAssets;
    const curPos = Object.values(portfolio.holdings).reduce((sum, h) => sum + (h.total_cost || 0), 0);
    if (curPos + amount > maxPos) {
      return { pass: false, reason: `总仓位将超上限（≤${(userCfg.max_position * 100).toFixed(0)}%），当前+拟买超限` };
    }
  }
  return { pass: true, reason: '' };
}

// 记录风控事件（risk_events）
function logRiskEvent(userId, eventType, fundCode, detail, action) {
  db.run(`INSERT INTO risk_events (user_id, event_type, fund_code, detail, action) VALUES (?, ?, ?, ?, ?)`,
    [userId, eventType, fundCode || '', detail || '', action || ''], (err) => {
      if (err) console.error('风控事件写入失败:', err.message);
    });
  audit('risk-engine', 'RISK_EVENT', userId + ' ' + fundCode, { eventType, detail, action });
}

// ============ P0-3 绩效与报告（规格 §4.5/§5.2）============

// 抓取沪深300指数收盘点位（东方财富 K 线接口，UTF-8 JSON，真实数据）
async function fetchBenchmark() {
  try {
    const url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get';
    let resp = null;
    for (let attempt = 0; attempt < 3 && !resp; attempt++) {
      try {
        resp = await axios.get(url, {
          params: {
            secid: '1.000300', fields1: 'f1,f2,f3,f4,f5,f6',
            fields2: 'f51,f53', klt: '101', fqt: '0',
            beg: '20260101', end: '20500101', lmt: '15'
          },
          timeout: 12000
        });
      } catch (e) {
        if (attempt < 2) { await new Promise(r => setTimeout(r, 3000)); }
        else throw e;
      }
    }
    const klines = resp.data && resp.data.data && resp.data.data.klines;
    if (!klines || !klines.length) { console.error('[基准] 沪深300 K线为空'); return 0; }
    let saved = 0;
    for (const k of klines) {
      const parts = k.split(',');
      const date = parts[0], close = parseFloat(parts[1]);
      if (!date || isNaN(close)) continue;
      const prev = await new Promise((resolve) => {
        db.get('SELECT value FROM benchmark_daily WHERE date < ? ORDER BY date DESC LIMIT 1', [date], (err, row) => resolve(err ? null : (row ? row.value : null)));
      });
      const chg = prev ? ((close / prev - 1) * 100) : 0;
      await new Promise((resolve) => {
        db.run('INSERT OR REPLACE INTO benchmark_daily (date, value, change_pct) VALUES (?, ?, ?)', [date, close, chg], (err) => resolve());
      });
      saved++;
    }
    console.log(`[基准] 沪深300 已更新 ${saved} 个交易日，最新: ${klines[klines.length - 1]}`);
    return saved;
  } catch (e) {
    console.error('[基准] 抓取失败:', e.message);
    return 0;
  }
}

// 计算某用户某日绩效指标（收益/超额/波动/夏普/回撤）写入 performance_daily
async function computePerformance(userId, dateStr) {
  const pf = await getUserPortfolio(userId);
  const initial = userConfigs[userId]?.initial_capital || 100000;
  // 总资产 = 现金 + 持仓市值（getUserPortfolio 不返回 total_assets，需自算）
  let marketValue = 0;
  for (const [code, h] of Object.entries(pf.holdings)) {
    const navRow = await new Promise((resolve) => {
      db.get('SELECT unit_nav FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1', [code], (err, row) => resolve(err ? null : row));
    });
    if (navRow && navRow.unit_nav) marketValue += h.shares * navRow.unit_nav;
  }
  const totalAssets = pf.current_capital + marketValue;
  const totalReturn = initial > 0 ? (totalAssets / initial - 1) * 100 : 0;

  // 基准收益：从组合首个快照日对应的基准点位起算（对齐组合起点，避免全历史偏差）
  const benchRow = await new Promise((resolve) => {
    db.get('SELECT value FROM benchmark_daily WHERE date <= ? ORDER BY date DESC LIMIT 1', [dateStr], (err, row) => resolve(err ? null : row));
  });
  const firstSnap = await new Promise((resolve) => {
    db.get('SELECT date FROM portfolio_daily WHERE user_id = ? ORDER BY date ASC LIMIT 1', [userId], (err, row) => resolve(err ? null : row));
  });
  const benchFirst = await new Promise((resolve) => {
    db.get('SELECT value FROM benchmark_daily WHERE date <= ? ORDER BY date DESC LIMIT 1', [firstSnap ? firstSnap.date : dateStr], (err, row) => resolve(err ? null : row));
  });
  const benchReturn = (benchFirst && benchFirst.value > 0 && benchRow && benchRow.value > 0)
    ? ((benchRow.value / benchFirst.value - 1) * 100) : 0;
  const excessReturn = totalReturn - benchReturn;

  // 近 20 日每日收益（基于 portfolio_daily）→ 年化波动 + 夏普
  const daily = await new Promise((resolve) => {
    db.all('SELECT date, total_assets, daily_pnl FROM portfolio_daily WHERE user_id = ? AND date <= ? ORDER BY date DESC LIMIT 21', [userId, dateStr], (err, rows) => resolve(err ? [] : (rows || [])));
  });
  daily.reverse();
  let volatility = 0, sharpe = 0;
  if (daily.length >= 5) {
    const rets = [];
    for (let i = 1; i < daily.length; i++) {
      const prev = daily[i - 1].total_assets;
      if (prev > 0) rets.push((daily[i].total_assets - prev) / prev);
    }
    if (rets.length >= 4) {
      const mean = rets.reduce((a, b) => a + b, 0) / rets.length;
      const variance = rets.reduce((a, b) => a + (b - mean) * (b - mean), 0) / (rets.length - 1);
      const dailyVol = Math.sqrt(variance);
      volatility = dailyVol * Math.sqrt(252) * 100;
      const annualRet = mean * 252 * 100;
      sharpe = volatility > 0 ? ((annualRet - 2) / volatility) : 0; // 无风险 2%
    }
  }

  // 最大回撤（截至今日，基于历史快照峰值）
  const dd = await getPortfolioDrawdown(userId);

  await new Promise((resolve) => {
    db.run(`INSERT INTO performance_daily (user_id, date, total_return, benchmark_return, excess_return, volatility, sharpe, max_drawdown) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET total_return=excluded.total_return, benchmark_return=excluded.benchmark_return,
            excess_return=excluded.excess_return, volatility=excluded.volatility, sharpe=excluded.sharpe, max_drawdown=excluded.max_drawdown`,
      [userId, dateStr, totalReturn, benchReturn, excessReturn, volatility, sharpe, dd || 0], (err) => resolve());
  });
  return { userId, dateStr, totalReturn, benchReturn, excessReturn, volatility, sharpe, maxDrawdown: dd };
}

// 生成报告（周报/月报），写入 reports 表；内容与交易流水/快照可对账
async function generateReport(userId, reportType) {
  const cfg = userConfigs[userId] || {};
  const now = new Date();
  let period, rangeDesc;
  const dateStr = getLocalDateStr();
  if (reportType === 'weekly') {
    const d = new Date(now); d.setDate(d.getDate() - 7);
    period = d.toISOString().slice(0, 10) + ' ~ ' + dateStr;
    rangeDesc = '近7天';
  } else {
    const d = new Date(now); d.setDate(d.getDate() - 30);
    period = d.toISOString().slice(0, 10) + ' ~ ' + dateStr;
    rangeDesc = '近30天';
  }

  const pf = await getUserPortfolio(userId);
  let marketValueR = 0;
  for (const [code, h] of Object.entries(pf.holdings)) {
    const navR = await new Promise((resolve) => {
      db.get('SELECT unit_nav FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1', [code], (err, row) => resolve(err ? null : row));
    });
    if (navR && navR.unit_nav) marketValueR += h.shares * navR.unit_nav;
  }
  const totalAssetsReport = pf.current_capital + marketValueR;
  const perf = await new Promise((resolve) => {
    db.get('SELECT * FROM performance_daily WHERE user_id = ? ORDER BY date DESC LIMIT 1', [userId], (err, row) => resolve(err ? null : row));
  });
  const trades = await new Promise((resolve) => {
    db.all('SELECT * FROM transactions WHERE user_id = ? AND transaction_date >= date(?) ORDER BY transaction_date', [userId, period.split(' ~ ')[0]], (err, rows) => resolve(err ? [] : (rows || [])));
  });
  const events = await new Promise((resolve) => {
    db.all('SELECT * FROM risk_events WHERE user_id = ? AND created_at >= datetime(?) ORDER BY id', [userId, period.split(' ~ ')[0] + ' 00:00:00'], (err, rows) => resolve(err ? [] : (rows || [])));
  });
  const orders = await new Promise((resolve) => {
    db.all("SELECT * FROM orders WHERE user_id = ? AND order_date >= ? AND status IN ('DONE','CONFIRMED') ORDER BY order_date", [userId, period.split(' ~ ')[0]], (err, rows) => resolve(err ? [] : (rows || [])));
  });

  const lines = [];
  lines.push(`# ${cfg.name}（${cfg.style}）${reportType === 'weekly' ? '周报' : '月报'} ${rangeDesc}`);
  lines.push('');
  lines.push(`报告周期：${period}`);
  lines.push(`当前总资产：¥${totalAssetsReport.toFixed(2)}（初始 ¥${pf.initial_capital}）`);
  lines.push(`累计收益：${(perf ? perf.total_return : 0).toFixed(2)}%`);
  lines.push(`基准（沪深300）同期：${(perf ? perf.benchmark_return : 0).toFixed(2)}%`);
  lines.push(`超额收益：${(perf ? perf.excess_return : 0).toFixed(2)}%`);
  if (perf) {
    lines.push(`年化波动率：${perf.volatility.toFixed(2)}%　夏普比率：${perf.sharpe.toFixed(2)}`);
    lines.push(`最大回撤：${(perf.max_drawdown || 0).toFixed(2)}%`);
  }
  lines.push('');
  lines.push('## 持仓明细');
  for (const [code, h] of Object.entries(pf.holdings)) {
    const nav = await new Promise((resolve) => {
      db.get('SELECT unit_nav FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1', [code], (err, row) => resolve(err ? null : row));
    });
    const mv = nav && nav.unit_nav ? h.shares * nav.unit_nav : h.total_cost;
    lines.push(`- ${code}：${h.shares}份　成本¥${h.total_cost.toFixed(2)}　市值约¥${mv.toFixed(2)}　盈亏 ${h.cost > 0 ? ((((nav ? nav.unit_nav : h.cost) / h.cost) - 1) * 100).toFixed(2) + '%' : '-'}`);
  }
  lines.push('');
  lines.push('## 期间交易');
  if (trades.length === 0 && orders.length === 0) lines.push('- 无成交');
  for (const o of orders) lines.push(`- [订单#${o.id}] ${o.fund_code} ${o.order_type} ${o.order_type === 'BUY' ? '¥' + o.amount : o.shares + '份'} ${o.order_date}（${o.reason || ''}）`);
  lines.push('');
  lines.push('## 风控事件');
  if (events.length === 0) lines.push('- 无');
  for (const ev of events) lines.push(`- [${ev.event_type}] ${ev.fund_code || ''} ${ev.detail}（${utcToLocalStr(ev.created_at)}）`);
  lines.push('');
  if (reportType === 'monthly') {
    // 业绩归因（简化 Brinson）：配置贡献 vs 选基贡献（设计文档 §4.7）
    try {
      const attr = await performanceAttribution(userId);
      lines.push('## 业绩归因（简化 Brinson）');
      lines.push(`- 配置贡献：${attr.allocation.toFixed(2)}%　选基贡献：${attr.selection.toFixed(2)}%　总超额：${attr.totalExcess.toFixed(2)}%`);
      lines.push('');
    } catch (e) {
      lines.push('## 业绩归因');
      lines.push(`- 计算失败：${e.message}`);
      lines.push('');
    }
    // 费用统计：期间交易费用（与交易流水可对账）+ 累计费用
    let periodBuy = 0, periodSell = 0;
    (trades || []).forEach(t => { if (t.transaction_type === 'BUY') periodBuy += t.fees || 0; else if (t.transaction_type === 'SELL') periodSell += t.fees || 0; });
    const feeAll = await new Promise((resolve) => {
      db.all('SELECT transaction_type, SUM(fees) AS fee FROM transactions WHERE user_id = ? GROUP BY transaction_type', [userId], (err, rows) => {
        let b = 0, g = 0; (rows || []).forEach(r => { if (r.transaction_type === 'BUY') b += r.fee || 0; else if (r.transaction_type === 'SELL') g += r.fee || 0; });
        resolve({ b, g });
      });
    });
    lines.push('## 费用统计');
    lines.push(`- 期间交易费用：申购费 ¥${periodBuy.toFixed(2)}　赎回费 ¥${periodSell.toFixed(2)}（合计 ¥${(periodBuy + periodSell).toFixed(2)}）`);
    lines.push(`- 累计费用：申购费 ¥${feeAll.b.toFixed(2)}　赎回费 ¥${feeAll.g.toFixed(2)}（合计 ¥${(feeAll.b + feeAll.g).toFixed(2)}）`);
    lines.push('');
  }
  // 期间每日收益明细（快照口径）——周报专属
  if (reportType === 'weekly') {
    const snapWeek = await new Promise((resolve) => {
      db.all('SELECT date, daily_pnl FROM portfolio_daily WHERE user_id = ? AND date >= ? ORDER BY date', [userId, period.split(' ~ ')[0]], (err, rows) => resolve(err ? [] : (rows || [])));
    });
    if (snapWeek.length) {
      const weekTotal = snapWeek.reduce((a, x) => a + (x.daily_pnl || 0), 0);
      lines.push('## 期间每日收益（快照口径）');
      for (const x of snapWeek) lines.push(`- ${x.date}：${x.daily_pnl >= 0 ? '+' : ''}¥${x.daily_pnl.toFixed(2)}`);
      lines.push(`- 本周合计：${weekTotal >= 0 ? '+' : ''}¥${weekTotal.toFixed(2)}`);
      lines.push('');
    }
    // AI 操盘点评（数据驱动）
    const buys = (trades || []).filter(t => t.transaction_type === 'BUY').length;
    const sells = (trades || []).filter(t => t.transaction_type === 'SELL').length;
    const realized = await new Promise((resolve) => {
      db.all('SELECT amount FROM realized_pnl WHERE user_id = ? AND created_at >= datetime(?)', [userId, period.split(' ~ ')[0] + ' 00:00:00'], (err, rows) => resolve(err ? [] : (rows || [])));
    });
    const realizedTotal = realized.reduce((a, r) => a + (r.amount || 0), 0);
    const snapSum = snapWeek.reduce((a, x) => a + (x.daily_pnl || 0), 0);
    let tone;
    if (snapSum >= 0 && snapSum < 100) tone = '本周账户小幅盈利，走势平稳，未出现明显回撤。';
    else if (snapSum >= 100) tone = '本周账户表现积极，收益为正，主要受益于持仓净值上行。';
    else if (snapSum >= -100) tone = '本周账户小幅回撤，属正常波动区间，未触发风控红线。';
    else tone = '本周账户回撤明显，AI 已按风控规则评估减仓/止损，避免更大损失。';
    const op = [];
    if (buys > 0) op.push(`主动买入 ${buys} 笔`); else op.push('未新增建仓');
    if (sells > 0) op.push(`卖出/减仓 ${sells} 笔，实现盈亏 ${realizedTotal >= 0 ? '+' : ''}¥${realizedTotal.toFixed(2)}`); else op.push('未触发卖出');
    lines.push('## AI 操盘点评');
    lines.push(tone);
    lines.push(`- 本周操作：${op.join('；')}；`);
    lines.push(`- 事件数：${events.length} 条风控记录${events.length ? '，已按规则处理' : '，市场平稳'};`);
    lines.push(`- 观察池跟踪 ${Object.keys(pf.holdings).length} 只持仓 + ${(await new Promise((resolve) => db.get('SELECT COUNT(*) c FROM watchlist WHERE user_id = ?', [userId], (e, r) => resolve(r || { c: 0 })))).c} 只观察标的。`);
    lines.push('');
  }
  lines.push('## 下周计划');
  lines.push(`- 按 ${cfg.rebalance_frequency || 'monthly'} 再平衡节奏评估调仓；`);
  lines.push(`- 观察池 ${cfg.watchlist_style || ''} 标的持续跟踪，${cfg.entry_signal_threshold || 'strong'} 信号才建仓；`);
  lines.push(`- 止损线 -${((cfg.stop_loss || 0.05) * 100).toFixed(0)}%，止盈线 +${((cfg.take_profit || 0.2) * 100).toFixed(0)}%，回撤熔断 -${((cfg.max_drawdown || 0.1) * 100).toFixed(0)}%。`);

  const content = lines.join('\n');
  await new Promise((resolve) => {
    // 同周期去重：先删同 (user_id, report_type, period) 旧报告，再插入最新——避免手动/调度重复生成堆积
    db.run('DELETE FROM reports WHERE user_id = ? AND report_type = ? AND period = ?', [userId, reportType, period], (err) => {
      db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, reportType, period, content], (err2) => resolve());
    });
  });
  return { userId, reportType, period, content };
}

// ============ P1 决策质量（规格 §4.2/§4.3/§4.5/§4.6/§4.7）============

// 基金评分/风格定位：基于 fund_nav 近60日真实净值计算波动/下行风险/风格标签/综合分
async function computeFundProfiles() {
  const codes = await new Promise((resolve) => {
    db.all('SELECT fund_code FROM funds', [], (err, rows) => resolve(err ? [] : (rows || []).map(r => r.fund_code)));
  });
  let done = 0;
  for (const code of codes) {
    const rows = await new Promise((resolve) => {
      db.all('SELECT nav_date, unit_nav, daily_return FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 61', [code], (err, rows) => resolve(err ? [] : (rows || [])));
    });
    if (rows.length < 20) continue;
    rows.reverse();
    const rets = [];
    for (let i = 1; i < rows.length; i++) {
      if (rows[i - 1].unit_nav > 0) rets.push((rows[i].unit_nav - rows[i - 1].unit_nav) / rows[i - 1].unit_nav);
    }
    if (rets.length < 15) continue;
    const mean = rets.reduce((a, b) => a + b, 0) / rets.length;
    const variance = rets.reduce((a, b) => a + (b - mean) * (b - mean), 0) / (rets.length - 1);
    const vol = Math.sqrt(variance) * Math.sqrt(252) * 100;
    const downside = rets.filter(r => r < 0).reduce((a, b) => a + b * b, 0) / Math.max(1, rets.filter(r => r < 0).length);
    const downsideRisk = Math.sqrt(downside) * Math.sqrt(252) * 100;
    // 区间收益（近60日）
    const periodRet = rows.length > 20 ? ((rows[rows.length - 1].unit_nav / rows[Math.max(0, rows.length - 21)].unit_nav - 1) * 100) : 0;
    // 风格标签：按波动率/下行风险聚类
    let styleLabel;
    if (vol < 15) styleLabel = '稳健型';
    else if (vol < 30) styleLabel = '均衡型';
    else if (vol < 45) styleLabel = '成长型';
    else styleLabel = '高风险高弹性';
    // 综合评分（收益/风险调整，0-100）：收益正向、波动负向
    const score = Math.max(0, Math.min(100, Math.round(periodRet * 2 - vol * 0.8 + 50)));
    await new Promise((resolve) => {
      db.run(`INSERT INTO fund_profiles (fund_code, volatility, downside_risk, style_label, score, updated_at) VALUES (?, ?, ?, ?, ?, datetime("now","localtime"))
              ON CONFLICT(fund_code) DO UPDATE SET volatility=excluded.volatility, downside_risk=excluded.downside_risk,
              style_label=excluded.style_label, score=excluded.score, updated_at=excluded.updated_at`,
        [code, +vol.toFixed(2), +downsideRisk.toFixed(2), styleLabel, score], (err) => resolve());
    });
    done++;
  }
  console.log(`[评分] 已更新 ${done} 只基金画像（波动/下行/风格/评分）`);
  return done;
}

// 数据质量校验：净值突变 >±10% 或最新净值缺失 → 告警并记录
function checkDataQuality(code, navDate, dailyReturn) {
  if (dailyReturn != null && Math.abs(dailyReturn) > 10) {
    db.run('INSERT INTO data_quality_logs (fund_code, nav_date, issue_type, detail) VALUES (?, ?, ?, ?)',
      [code, navDate, 'NAV_JUMP', '单日净值波动 ' + dailyReturn.toFixed(2) + '% 超 ±10%，已标记'], (err) => {
        if (err) console.error('数据质量写入失败:', err.message);
      });
    return false;
  }
  return true;
}

// 市场温度：基金池平均日涨跌 + 沪深300 涨跌 → 温度（hot/warm/neutral/cold/frozen）
async function computeMarketEnv() {
  const dateStr = getLocalDateStr();
  const avg = await new Promise((resolve) => {
    db.all("SELECT daily_return FROM fund_nav WHERE nav_date = (SELECT MAX(nav_date) FROM fund_nav) AND daily_return IS NOT NULL", [], (err, rows) => {
      if (err || !rows || rows.length === 0) return resolve(null);
      resolve(rows.reduce((a, b) => a + b.daily_return, 0) / rows.length);
    });
  });
  const bench = await new Promise((resolve) => {
    db.get('SELECT change_pct FROM benchmark_daily ORDER BY date DESC LIMIT 1', [], (err, row) => resolve(err ? null : (row ? row.change_pct : null)));
  });
  let temperature = 'neutral';
  if (avg != null) {
    if (avg >= 1) temperature = 'hot';
    else if (avg >= 0.3) temperature = 'warm';
    else if (avg <= -1) temperature = 'frozen';
    else if (avg <= -0.3) temperature = 'cold';
  }
  await new Promise((resolve) => {
    db.run('INSERT OR REPLACE INTO market_env (date, avg_fund_chg, bench_chg, temperature, updated_at) VALUES (?, ?, ?, ?, datetime("now","localtime"))',
      [dateStr, avg != null ? +avg.toFixed(2) : null, bench != null ? +bench.toFixed(2) : null, temperature], (err) => resolve());
  });
  console.log(`[市场] ${dateStr} 基金均涨 ${avg != null ? avg.toFixed(2) + '%' : 'N/A'} 基准 ${bench != null ? bench.toFixed(2) + '%' : 'N/A'} 温度:${temperature}`);
  return temperature;
}

// 温度 → 建仓金额系数（cold/frozen 保守，hot/warm 积极）
function temperatureFactor(temp) {
  if (temp === 'frozen') return 0.5;
  if (temp === 'cold') return 0.8;
  if (temp === 'hot') return 1.2;
  if (temp === 'warm') return 1.1;
  return 1.0;
}

// 再平衡：按性格 base_weights 检查类型配置偏离，超阈值生成调仓订单（卖超配买低配）
async function rebalanceCheck(userId) {
  const cfg = await getRiskParams(userId);
  const freq = cfg.rebalance_frequency || 'monthly';
  // 频率判定：weekly 每周五；monthly 每月最后交易日（由调用处控制，这里只做执行）
  const pf = await getUserPortfolio(userId);
  const weights = cfg.base_weights || { '混合型': 0.5, '股票型': 0.3, '指数型': 0.2 };
  // 计算当前各类型市值
  const typeValues = {};
  let total = pf.current_capital;
  for (const [code, h] of Object.entries(pf.holdings)) {
    const fund = await new Promise((resolve) => {
      db.get('SELECT fund_type FROM funds WHERE fund_code = ?', [code], (err, row) => resolve(err ? null : row));
    });
    const navRow = await new Promise((resolve) => {
      db.get('SELECT unit_nav FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1', [code], (err, row) => resolve(err ? null : row));
    });
    const mv = navRow && navRow.unit_nav ? h.shares * navRow.unit_nav : h.total_cost;
    const type = fund ? fund.fund_type : '混合型';
    typeValues[type] = (typeValues[type] || 0) + mv;
    total += mv;
  }
  const ordersMade = [];
  const threshold = 0.15; // 偏离 15% 触发
  for (const [type, target] of Object.entries(weights)) {
    const cur = total > 0 ? ((typeValues[type] || 0) / total) : 0;
    if (cur - target > threshold) {
      // 超配 → 卖超配部分（按该类型持仓比例摊分，选一只卖）
      const over = (cur - target) * total;
      const sellAmt = Math.min(over, (typeValues[type] || 0) * 0.3);
      for (const [code, h] of Object.entries(pf.holdings)) {
        const fund = await new Promise((resolve) => {
          db.get('SELECT fund_type FROM funds WHERE fund_code = ?', [code], (err, row) => resolve(err ? null : row));
        });
        if (fund && fund.fund_type === type && h.shares > 0) {
          const navRow = await new Promise((resolve) => {
            db.get('SELECT unit_nav FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1', [code], (err, row) => resolve(err ? null : row));
          });
          if (!navRow || !navRow.unit_nav) continue;
          const sellShares = Math.max(1, Math.round(sellAmt / navRow.unit_nav));
          if (sellShares >= h.shares) continue; // 不满仓清仓（再平衡不全卖）
          const order = await orderEngine.createOrder({ db, audit }, {
            userId, fundCode: code, orderType: 'SELL', amount: 0, shares: sellShares, price: navRow.unit_nav,
            reason: `再平衡调仓：${type}超配 ${(cur * 100).toFixed(1)}%（目标 ${(target * 100).toFixed(0)}%），卖出降低`
          });
          ordersMade.push({ fund_code: code, type: 'SELL', shares: sellShares, orderId: order.id });
          logRiskEvent(userId, 'REBALANCE', code, `${type}超配→卖出 ${sellShares} 份`, 'sell');
          break;
        }
      }
    } else if (target - cur > threshold && total * 0.05 >= 100) {
      // 低配 → 买入该类型观察池基金（取分数最高的一只，风控约束）
      const buyAmt = Math.round((target - cur) * total * 0.3);
      if (buyAmt < 100) continue;
      const candidates = await new Promise((resolve) => {
        db.all(`SELECT w.fund_code FROM watchlist w JOIN funds f ON w.fund_code = f.fund_code
                 JOIN fund_profiles fp ON fp.fund_code = w.fund_code
                 WHERE w.user_id = ? AND f.fund_type = ? ORDER BY fp.score DESC LIMIT 1`, [userId, type], (err, rows) => resolve(err ? [] : (rows || [])));
      });
      if (!candidates.length) continue;
      const code = candidates[0].fund_code;
      const sig = await getFundSignal(code);
      if (!sig || !sig.latest_nav || !(sig.signal.action === 'buy' || sig.signal.action === 'add')) continue;
      const rc = await checkRiskControls(userId, pf, 'BUY', code, buyAmt, cfg);
      if (!rc.pass) {
        logRiskEvent(userId, 'REBALANCE_BLOCKED', code, rc.reason, 'block');
        continue;
      }
      const order = await orderEngine.createOrder({ db, audit }, {
        userId, fundCode: code, orderType: 'BUY', amount: buyAmt, price: sig.latest_nav,
        reason: `再平衡调仓：${type}低配 ${((target - cur) * 100).toFixed(1)}%，买入补足（信号 ${sig.signal.label}）`
      });
      ordersMade.push({ fund_code: code, type: 'BUY', amount: buyAmt, orderId: order.id });
    }
  }
  if (ordersMade.length) console.log(`[再平衡] ${userId} 生成调仓订单: `, JSON.stringify(ordersMade));
  else console.log(`[再平衡] ${userId} 配置偏离未超阈值，无需调仓`);
  return ordersMade;
}

// 换仓决策：观察池强信号 vs 持仓弱信号 → 卖出弱者买入强者（每周五评估，单次最多1组）
async function switchFunds(userId) {
  const pf = await getUserPortfolio(userId);
  const cfg = await getRiskParams(userId);
  // 持仓弱信号基金（近20日<-5% 且跌破20日线）
  let weakHolding = null;
  for (const [code, h] of Object.entries(pf.holdings)) {
    if (h.shares <= 0) continue;
    const sig = await getFundSignal(code);
    if (sig && sig.change_20d != null && sig.change_20d < -5 && sig.above_ma20 === false) {
      weakHolding = { code, h, sig };
      break;
    }
  }
  if (!weakHolding) return null;
  // 观察池强信号基金（buy + 评分高）
  const strong = await new Promise((resolve) => {
    db.all(`SELECT w.fund_code FROM watchlist w JOIN fund_profiles fp ON fp.fund_code = w.fund_code
             WHERE w.user_id = ? AND fp.score >= 60 ORDER BY fp.score DESC LIMIT 1`, [userId], (err, rows) => resolve(err ? [] : (rows || [])));
  });
  if (!strong.length) return null;
  const code = strong[0].fund_code;
  const sig = await getFundSignal(code);
  if (!sig || !sig.latest_nav || !(sig.signal.action === 'buy' || sig.signal.action === 'add')) return null;
  const nav = sig.latest_nav;
  const sellNav = weakHolding.sig.latest_nav;
  if (!sellNav) return null;
  // 卖弱（全卖）买强（等额，受风控与现金约束）
  const sellShares = weakHolding.h.shares;
  const estCash = sellShares * sellNav;
  const rc = await checkRiskControls(userId, pf, 'BUY', code, estCash, cfg);
  if (!rc.pass) {
    logRiskEvent(userId, 'SWITCH_BLOCKED', code, rc.reason, 'block');
    return null;
  }
  try {
    const sellOrder = await orderEngine.createOrder({ db, audit }, {
      userId, fundCode: weakHolding.code, orderType: 'SELL', amount: 0, shares: sellShares, price: sellNav,
      reason: `换仓决策：${weakHolding.code} 近20日 ${weakHolding.sig.change_20d.toFixed(1)}% 跌破20日线（弱信号），卖出换入强势基金`
    });
    const buyOrder = await orderEngine.createOrder({ db, audit }, {
      userId, fundCode: code, orderType: 'BUY', amount: Math.round(estCash), price: nav,
      reason: `换仓决策：买入 ${code}（评分高、信号 ${sig.signal.label}），承接换仓资金`
    });
    console.log(`[换仓] ${userId} 卖 ${weakHolding.code} 买 ${code}（订单#${sellOrder.id}/#${buyOrder.id}）`);
    logRiskEvent(userId, 'SWITCH', weakHolding.code + '→' + code, `卖出弱势换入强势（等额 ${Math.round(estCash)} 元）`, 'switch');
    return { sell: sellOrder.id, buy: buyOrder.id, from: weakHolding.code, to: code };
  } catch (e) {
    console.error('[换仓] 失败:', e.message);
    return null;
  }
}

// 分红/拆分处理：抓取天天基金分红记录 → 除息日自动现金分红到账+成本校正
async function dividendAdjust() {
  const codes = await new Promise((resolve) => {
    db.all('SELECT fund_code FROM funds', [], (err, rows) => resolve(err ? [] : (rows || []).map(r => r.fund_code)));
  });
  let found = 0;
  for (const code of codes) {
    try {
      const resp = await axios.get('https://api.fund.eastmoney.com/f10/F10DataApi', {
        params: { type: 'fhsp', code, page: 1, per: 5 },
        headers: { Referer: 'http://fundf10.eastmoney.com/', 'User-Agent': 'Mozilla/5.0' },
        timeout: 10000
      });
      const ls = resp.data && resp.data.Data && resp.data.Data.ls;
      if (!ls) continue;
      for (const item of ls) {
        const cells = item.replace(/<[^>]+>/g, '|').split('|').map(x => x.trim()).filter(Boolean);
        // 典型格式: 权益登记日 | 除息日 | 每份分红(元) | 分红发放日 | 分红类型...
        if (cells.length < 3) continue;
        const exDate = cells[1];
        const perUnit = parseFloat(cells[2]);
        if (!/^\d{4}-\d{2}-\d{2}$/.test(exDate) || isNaN(perUnit)) continue;
        await new Promise((resolve) => {
          db.run('INSERT OR IGNORE INTO dividends (fund_code, ex_date, per_unit, type) VALUES (?, ?, ?, ?)', [code, exDate, perUnit, 'CASH'], (err) => resolve());
        });
        found++;
        // 除息日为今日 → 现金分红落账（对持有该基金的用户）
        if (exDate === getLocalDateStr()) {
          for (const userId of Object.keys(userConfigs)) {
            const pf = await getUserPortfolio(userId);
            const h = pf.holdings[code];
            if (!h || h.shares <= 0) continue;
            const cashAmount = +(h.shares * perUnit).toFixed(2);
            if (cashAmount <= 0) continue;
            await new Promise((resolve) => {
              db.run('UPDATE users SET capital = capital + ? WHERE id = ?', [cashAmount, userId], (err) => resolve());
            });
            // 成本同步下降（除息）
            const newCost = Math.max(0, h.total_cost - cashAmount);
            await new Promise((resolve) => {
              db.run('UPDATE holdings SET total_cost = ? WHERE user_id = ? AND fund_code = ?', [newCost, userId, code], (err) => resolve());
            });
            db.run(`INSERT INTO transactions (user_id, fund_code, transaction_type, amount, price, shares, fees, reason)
                     VALUES (?, ?, 'DIVIDEND', ?, ?, ?, 0, ?)`,
              [userId, code, cashAmount, perUnit, 0, code + ' 现金分红 ¥' + cashAmount + '（每份 ¥' + perUnit + '）'], (err) => {});
            logRiskEvent(userId, 'DIVIDEND', code, '现金分红到账 ¥' + cashAmount, 'cash');
            console.log(`[分红] ${userId} 持有 ${code} 获现金分红 ¥${cashAmount}`);
          }
        }
      }
    } catch (e) {
      // 分红接口失败不阻塞（记录一次即可）
    }
  }
  if (found) console.log(`[分红] 已同步 ${found} 条分红记录`);
  return found;
}

// 业绩归因（简化 Brinson）：配置贡献 vs 选基贡献 → 写入月报
async function performanceAttribution(userId) {
  const pf = await getUserPortfolio(userId);
  const cfg = await getRiskParams(userId);
  const weights = cfg.base_weights || {};
  const perf = await new Promise((resolve) => {
    db.get('SELECT * FROM performance_daily WHERE user_id = ? ORDER BY date DESC LIMIT 1', [userId], (err, row) => resolve(err ? null : row));
  });
  if (!perf) return null;
  const totalExcess = perf.excess_return || 0;
  // 配置贡献：Σ(实际类型权重 - 目标权重) × 类型平均收益
  let allocContrib = 0;
  const typeValues = {};
  let total = pf.current_capital;
  for (const [code, h] of Object.entries(pf.holdings)) {
    const fund = await new Promise((resolve) => {
      db.get('SELECT fund_type FROM funds WHERE fund_code = ?', [code], (err, row) => resolve(err ? null : row));
    });
    const navRow = await new Promise((resolve) => {
      db.get('SELECT unit_nav FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1', [code], (err, row) => resolve(err ? null : row));
    });
    const mv = navRow && navRow.unit_nav ? h.shares * navRow.unit_nav : h.total_cost;
    const type = fund ? fund.fund_type : '混合型';
    typeValues[type] = (typeValues[type] || 0) + mv;
    total += mv;
  }
  for (const [type, target] of Object.entries(weights)) {
    const cur = total > 0 ? ((typeValues[type] || 0) / total) : 0;
    const typeAvgRet = await new Promise((resolve) => {
      db.all(`SELECT fp.fund_code FROM funds f JOIN fund_profiles fp ON fp.fund_code = f.fund_code WHERE f.fund_type = ? LIMIT 20`, [type], (err, rows) => resolve(err ? [] : (rows || [])));
    });
    let avgRet = 0;
    for (const r of typeAvgRet.slice(0, 5)) {
      const sig = await getFundSignal(r.fund_code);
      if (sig && sig.change_20d != null) avgRet += sig.change_20d;
    }
    avgRet = typeAvgRet.length ? avgRet / Math.min(5, typeAvgRet.length) : 0;
    allocContrib += (cur - target) * avgRet;
  }
  const selectContrib = totalExcess - allocContrib;
  return { allocation: +allocContrib.toFixed(2), selection: +selectContrib.toFixed(2), totalExcess: +totalExcess.toFixed(2) };
}

// 压力测试（月度）：模拟 -10%/-20% 情景 → 组合预估回撤报告
async function generatePressureReport(userId) {
  const pf = await getUserPortfolio(userId);
  let marketValue = 0;
  for (const [code, h] of Object.entries(pf.holdings)) {
    const navRow = await new Promise((resolve) => {
      db.get('SELECT unit_nav FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1', [code], (err, row) => resolve(err ? null : row));
    });
    if (navRow && navRow.unit_nav) marketValue += h.shares * navRow.unit_nav;
  }
  const total = pf.current_capital + marketValue;
  const cfg = userConfigs[userId] || {};
  const lines = [];
  lines.push('# ' + (cfg.name || userId) + ' 压力测试报告');
  lines.push('');
  lines.push('报告日期：' + getLocalDateStr());
  lines.push('当前总资产：¥' + total.toFixed(2) + '（持仓市值 ¥' + marketValue.toFixed(2) + '，仓位 ' + (total > 0 ? (marketValue / total * 100).toFixed(1) : 0) + '%）');
  lines.push('');
  for (const shock of [-10, -20]) {
    const loss = marketValue * shock / 100;
    const after = total + loss;
    const dd = total > 0 ? (loss / total * 100) : 0;
    const exceed = (cfg.max_drawdown || 0.1) * 100;
    lines.push('## 市场 -' + Math.abs(shock) + '% 情景');
    lines.push('- 持仓市值预估：¥' + (marketValue + loss).toFixed(2));
    lines.push('- 组合总资产预估：¥' + after.toFixed(2));
    lines.push('- 预估回撤：' + dd.toFixed(2) + '%（回撤熔断线 -' + exceed.toFixed(0) + '%）→ ' + (dd >= exceed ? '⚠ 触发熔断，需减仓/停止买入' : '可控范围'));
    lines.push('');
  }
  lines.push('## 压力测试结论');
  lines.push('- 持仓集中度：' + (total > 0 ? (marketValue / total * 100).toFixed(1) : 0) + '%' + (total > 0 && marketValue / total > (cfg.max_position || 0.6) ? '（超总仓位上限，需降仓）' : '（符合仓位上限）'));
  const content = lines.join('\n');
  await new Promise((resolve) => {
    db.run("DELETE FROM reports WHERE user_id = ? AND report_type = 'pressure' AND period = ?", [userId, getLocalDateStr()], (err) => {
      db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, 'pressure', getLocalDateStr(), content], (err2) => resolve());
    });
  });
  return { userId, reportType: 'pressure', content };
}

// 每日复盘摘要：今日操作/盈亏/事件/明日关注点
async function generateDailyRecap() {
  const dateStr = getLocalDateStr();
  for (const userId of Object.keys(userConfigs)) {
    const cfg = userConfigs[userId] || {};
    const pf = await getUserPortfolio(userId);
    const perf = await new Promise((resolve) => {
      db.get('SELECT * FROM performance_daily WHERE user_id = ? ORDER BY date DESC LIMIT 1', [userId], (err, row) => resolve(err ? null : row));
    });
    const orders = await new Promise((resolve) => {
      db.all('SELECT * FROM orders WHERE user_id = ? AND order_date = ? ORDER BY id', [userId, dateStr], (err, rows) => resolve(err ? [] : (rows || [])));
    });
    const events = await new Promise((resolve) => {
      db.all("SELECT * FROM risk_events WHERE user_id = ? AND created_at >= datetime(?) ORDER BY id", [userId, dateStr + ' 00:00:00'], (err, rows) => resolve(err ? [] : (rows || [])));
    });
    const env = await new Promise((resolve) => {
      db.get('SELECT * FROM market_env WHERE date = ?', [dateStr], (err, row) => resolve(err ? null : row));
    });
    const snap = await new Promise((resolve) => {
      db.get('SELECT * FROM portfolio_daily WHERE user_id = ? AND date = ?', [userId, dateStr], (err, row) => resolve(err ? null : row));
    });
    const lines = [];
    lines.push('# ' + (cfg.name || userId) + ' 每日复盘 ' + dateStr);
    lines.push('');
    lines.push('## 今日市场');
    lines.push('- 基金池平均：' + (env && env.avg_fund_chg != null ? env.avg_fund_chg + '%' : 'N/A') + '；沪深300：' + (env && env.bench_chg != null ? env.bench_chg + '%' : 'N/A') + '；温度：' + (env ? env.temperature : 'N/A'));
    lines.push('');
    lines.push('## 今日账户');
    lines.push('- 总资产：¥' + pf.current_capital.toFixed(2) + '（现金）+ 持仓（见持仓页）');
    lines.push('- 当日盈亏：¥' + (snap ? snap.daily_pnl.toFixed(2) : 'N/A') + '；累计收益：' + (perf ? perf.total_return.toFixed(2) + '%' : 'N/A'));
    lines.push('');
    lines.push('## 今日操作');
    if (!orders.length) lines.push('- 无订单（或订单待 T+1 确认）');
    for (const o of orders) lines.push('- [订单#' + o.id + '] ' + o.fund_code + ' ' + o.order_type + ' ' + (o.order_type === 'BUY' ? '¥' + o.amount : o.shares + '份') + '：' + (o.reason || ''));
    lines.push('');
    lines.push('## 今日事件');
    if (!events.length) lines.push('- 无');
    for (const ev of events) lines.push('- [' + ev.event_type + '] ' + (ev.fund_code || '') + ' ' + (ev.detail || ''));
    lines.push('');
    lines.push('## 明日关注');
    lines.push('- ' + (cfg.name || userId) + '（' + (cfg.style || '') + '）：止损线 -' + ((cfg.stop_loss || 0.05) * 100).toFixed(0) + '%，止盈线 +' + ((cfg.take_profit || 0.2) * 100).toFixed(0) + '%');
    lines.push('- 关注持仓退场信号与观察池入场信号，' + (cfg.watchlist_style || '') + ' 方向标的优先');
    const content = lines.join('\n');
    await new Promise((resolve) => {
      db.run("DELETE FROM reports WHERE user_id = ? AND report_type = 'daily' AND period = ?", [userId, dateStr], (err) => {
        db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, 'daily', dateStr, content], (err2) => resolve());
      });
    });
    console.log('[复盘] ' + userId + ' 每日复盘已生成');
  }
}

// 盘后订单确认任务：每日 20:00 确认前一日（含更早）SUBMITTED 订单（T+1 规则）
function schedulePostCloseConfirmation() {
  const run = () => {
    confirmPendingOrders({ db, saveTransaction, updateHolding, audit }).then(r => {
      console.log(`[订单确认] 完成 ${r.confirmed} 笔` + (r.errors.length ? `，错误: ${r.errors.join('; ')}` : ''));
    }).catch(e => console.error('[订单确认] 失败:', e.message));
  };
  const now = new Date();
  const target = new Date(now);
  target.setHours(20, 0, 0, 0);
  if (now > target) target.setDate(target.getDate() + 1);
  const delay = target.getTime() - now.getTime();
  console.log(`[订单确认] 下次确认: ${target.toLocaleString('zh-CN')}`);
  setTimeout(() => {
    run();
    setInterval(run, 24 * 60 * 60 * 1000);
  }, delay);
}

function getUserWatchlistCodes(userId) {
  return new Promise((resolve, reject) => {
    db.all('SELECT fund_code FROM watchlist WHERE user_id = ?', [userId], (err, rows) => {
      if (err) reject(err);
      else resolve((rows || []).map(r => r.fund_code));
    });
  });
}

// 单只基金的真实走势信号（供 AI 决策与定时分析复用）
function getFundSignal(code) {
  return new Promise((resolve, reject) => {
    const sql = `
      SELECT
        (SELECT unit_nav FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1) AS latest_nav,
        (SELECT daily_return FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1) AS daily_return,
        (SELECT nav_date FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1) AS nav_date,
        (SELECT unit_nav FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1 OFFSET 5) AS nav_5d_ago,
        (SELECT unit_nav FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1 OFFSET 20) AS nav_20d_ago,
        (SELECT MAX(unit_nav) FROM (SELECT unit_nav FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 60)) AS high_60d,
        (SELECT AVG(unit_nav) FROM (SELECT unit_nav FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 20)) AS ma20
    `;
    db.get(sql, [code, code, code, code, code, code, code], (err, row) => {
      if (err) reject(err);
      else if (!row) resolve(null);
      else {
        const signal = buildWatchSignal(row);
        resolve({
          latest_nav: row.latest_nav,
          daily_return: row.daily_return,
          nav_date: row.nav_date,
          change_5d: row.change_5d,
          change_20d: row.change_20d,
          drawdown_60d: row.drawdown_60d,
          above_ma20: row.above_ma20,
          signal
        });
      }
    });
  });
}

// 全基金池真实指标（与 getWatchlist 同构，基于 funds 全表）
function getAllFundSignals() {
  return new Promise((resolve, reject) => {
    const sql = `
      SELECT f.fund_code, f.fund_name, f.fund_type,
             (SELECT unit_nav FROM fund_nav WHERE fund_code = f.fund_code ORDER BY nav_date DESC LIMIT 1) AS latest_nav,
             (SELECT nav_date FROM fund_nav WHERE fund_code = f.fund_code ORDER BY nav_date DESC LIMIT 1) AS nav_date,
             (SELECT unit_nav FROM fund_nav WHERE fund_code = f.fund_code ORDER BY nav_date DESC LIMIT 1 OFFSET 5) AS nav_5d_ago,
             (SELECT unit_nav FROM fund_nav WHERE fund_code = f.fund_code ORDER BY nav_date DESC LIMIT 1 OFFSET 20) AS nav_20d_ago,
             (SELECT MAX(unit_nav) FROM (SELECT unit_nav FROM fund_nav WHERE fund_code = f.fund_code ORDER BY nav_date DESC LIMIT 60)) AS high_60d,
             (SELECT AVG(unit_nav) FROM (SELECT unit_nav FROM fund_nav WHERE fund_code = f.fund_code ORDER BY nav_date DESC LIMIT 20)) AS ma20
      FROM funds f
    `;
    db.all(sql, [], (err, rows) => {
      if (err) reject(err);
      else resolve((rows || []).map(row => {
        const signal = buildWatchSignal(row);
        return {
          fund_code: row.fund_code,
          fund_name: row.fund_name,
          fund_type: row.fund_type,
          latest_nav: row.latest_nav,
          nav_date: row.nav_date,
          change_5d: row.change_5d,
          change_20d: row.change_20d,
          drawdown_60d: row.drawdown_60d,
          above_ma20: row.above_ma20,
          signal
        };
      }));
    });
  });
}

// 近20日日收益波动率（%）
function getVolatility(code) {
  return new Promise((resolve, reject) => {
    db.all('SELECT unit_nav FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 21', [code], (err, rows) => {
      if (err) reject(err);
      else {
        try {
          const navs = (rows || []).map(r => r.unit_nav).reverse();
          if (navs.length < 3) return resolve(null);
          const rets = [];
          for (let i = 1; i < navs.length; i++) {
            if (navs[i - 1] > 0) rets.push(navs[i] / navs[i - 1] - 1);
          }
          const mean = rets.reduce((s, v) => s + v, 0) / rets.length;
          const variance = rets.reduce((s, v) => s + (v - mean) * (v - mean), 0) / rets.length;
          resolve(Number((Math.sqrt(variance) * 100).toFixed(2)));
        } catch (e) {
          resolve(null);
        }
      }
    });
  });
}

// 观察池互斥锁：避免启动自动选基与用户手动触发/定时分析并发竞态（先删后插必须串行）
let discoverLock = null;
async function aiDiscoverWatchlist(userId) {
  while (discoverLock) await new Promise(r => setTimeout(r, 400));
  discoverLock = true;
  try {
    return await aiDiscoverWatchlistInner(userId);
  } finally {
    discoverLock = false;
  }
}

// AI 按用户性格从全市场自主选基并维护观察池（source='ai'，上限 KEEP 只；手动项永不删除；只影响观察池，不涉及交易）
// 候选池 = 全市场基金库 fund_universe（天天基金排行快照，股票型/混合型/指数型/QDII 共 1.4万+ 只）
async function aiDiscoverWatchlistInner(userId) {
  const user = userConfigs[userId];
  if (!user) throw new Error('用户不存在');
  const style = user.style || '稳健型';
  const risk = user.risk_tolerance || 'medium';

  // 现有观察池：区分手动（保留）与 AI（由 AI 重排维护）
  const existing = await getWatchlist(userId);
  const manualSet = new Set(existing.filter(x => x.source !== 'ai').map(x => x.fund_code));
  const aiSet = new Set(existing.filter(x => x.source === 'ai').map(x => x.fund_code));

  // 跨用户去重：其他用户的观察池（全部来源）与持仓，本用户 AI 不再重复关注（性格分工）
  const otherWatchSet = await new Promise((resolve) => {
    db.all('SELECT DISTINCT fund_code FROM watchlist WHERE user_id != ?', [userId], (err, rows) => {
      resolve(err ? new Set() : new Set((rows || []).map(r => r.fund_code)));
    });
  });
  const otherHoldSet = await new Promise((resolve) => {
    db.all('SELECT DISTINCT fund_code FROM holdings WHERE user_id != ? AND shares > 0', [userId], (err, rows) => {
      resolve(err ? new Set() : new Set((rows || []).map(r => r.fund_code)));
    });
  });

  // 全市场候选：fund_universe（含多周期涨幅快照）
  const universe = await new Promise((resolve) => {
    db.all('SELECT fund_code, fund_name, fund_type, unit_nav, day_return, r1m, r3m, r6m, r1y, inception_date, scale FROM fund_universe',
      (err, rows) => resolve(err ? [] : (rows || [])));
  });
  console.log(`[全市场选基] ${userId}（${style}）全市场候选 ${universe.length} 只`);

  const THEME_RE = /新能源|光伏|锂电|储能|风电|白酒|食品饮料|能源|石油|煤炭|钢铁|有色|化工|农业|养殖|消费|医药|医疗|生物|创新药|军工|国防|半导体|芯片|集成电路|电子|计算机|软件|信创|通信|5G|传媒|游戏|互联网|人工智能|AI|机器人|汽车|智能汽车|科创|创业板|专精特新|数字经济|云计算|大数据|数字|高端装备|高端制造|制造|改革|央企|国企|红利|环保|碳中和|基建|地产|银行|券商|保险|黄金|贵金属|原油|材料|设备|主题|科技|成长|创新|信息|转型|升级/;
  const MIN_SCALE = 2;             // 剔除迷你基金（规模 < 2 亿元）
  const CUTOFF_DATE = '2025-09-18'; // 成立满 1 年才参与（有完整周期可评分）

  const candidates = [];
  for (const f of universe) {
    if (!f.unit_nav || f.unit_nav <= 0) continue;
    if (f.scale != null && f.scale < MIN_SCALE) continue;
    if (f.inception_date && f.inception_date > CUTOFF_DATE) continue;
    if (manualSet.has(f.fund_code)) continue;
    if (otherWatchSet.has(f.fund_code)) continue;
    if (otherHoldSet.has(f.fund_code)) continue;

    const theme = THEME_RE.test(f.fund_name || '');
    const r1y = f.r1y != null ? f.r1y : 0;
    const r3m = f.r3m != null ? f.r3m : 0;
    const r6m = f.r6m != null ? f.r6m : 0;
    const day = f.day_return != null ? f.day_return : 0;

    let matched = false;
    let score = 0;
    if (risk === 'high') {
      // 激进：高弹性（近1年 >40%）∪ 高弹性类型（股票型/QDII）∪ 任何行业主题基金
      // 弹性 = 强动量 + 主题溢价 + 超跌反弹空间
      if (f.fund_type === '股票型' || f.fund_type === 'QDII' || theme || r1y > 40) matched = true;
      if (matched) {
        score = Math.max(r1y, 0) * 0.5 + Math.max(r3m, 0) * 0.6 + Math.max(day, 0) * 1.2
          + (theme ? 3 : 0) + (f.fund_type === '股票型' ? 2 : 0)
          + (r6m < 0 ? Math.min(Math.abs(r6m) * 0.15, 5) : 0);
      }
    } else {
      // 稳健：宽基指数（指数型）∪ 收益温和的均衡混合（近1年 <40% 且非主题）；稳定 = 长期正收益 + 回撤控制
      if ((f.fund_type === '指数型' && !theme) || (f.fund_type === '混合型' && !theme && r1y < 40)) matched = true;
      if (matched) {
        score = Math.max(r1y, 0) * 0.5 + Math.max(r6m, 0) * 0.3 + Math.max(day, 0) * 0.3
          + (r3m >= 0 ? 1.0 : 0) + (r6m < -15 ? -4 : 0) + (f.fund_type === '指数型' ? 6 : 0);
      }
    }
    if (!matched) continue;
    candidates.push({ fund_code: f.fund_code, fund_name: f.fund_name, fund_type: f.fund_type, score: Number(score.toFixed(2)), unit_nav: f.unit_nav, r1y, r6m, day });
  }

  candidates.sort((a, b) => b.score - a.score);
  // 观察池不设固定上限：AI 按全市场扫描排名动态维持（排名靠前即入池、掉队自动淘汰）。
  // MAX_POOL 仅为防御性上限（防止净值拉取与页面压力），手动添加的自选不限量。
  const MAX_POOL = 25;

  // 同策略 A/C/D 份额去重：同一基金只留评分最高的一只（避免观察池被重复份额占位）
  const seenKey = new Set();
  const deduped = [];
  for (const cd of candidates) {
    const key = (cd.fund_name || '').replace(/[ACDE]$/, '');
    if (seenKey.has(key)) continue;
    seenKey.add(key);
    deduped.push(cd);
  }

  const inserted = [];
  // AI 池全量重建：先清空本用户全部 AI 项，再写入最新扫描排名（观察池随市场动态流动）
  const removedCount = await new Promise((resolve, reject) => {
    db.run("DELETE FROM watchlist WHERE user_id = ? AND source = 'ai'", [userId], function (err) {
      if (err) reject(err); else resolve(this.changes || 0);
    });
  });
  // 候选顺位队列：净值不足 30 条的新基金跳过并自动补位（宁缺毋滥，尽量凑满观察池）
  const pickedQueue = deduped.slice(0, Math.max(MAX_POOL, Math.min(deduped.length, MAX_POOL * 3)));
  for (const fund of pickedQueue) {
    // 新基金：入库 funds + 拉全量历史净值；净值不足 30 条的不入池（无法出信号）
    if (inserted.length >= MAX_POOL) break;
    const navCount = await ensureFundWithNav(fund);
    if (navCount < 30) continue;
    const reason = `AI按${style}自动筛选（全市场 ${candidates.length} 只候选）：近1年 ${fund.r1y >= 0 ? '+' : ''}${fund.r1y}%，近6月 ${fund.r6m >= 0 ? '+' : ''}${fund.r6m}%，日增长 ${fund.day >= 0 ? '+' : ''}${fund.day}%`;
    await new Promise((resolve, reject) => {
      db.run("INSERT OR IGNORE INTO watchlist (user_id, fund_code, reason, source) VALUES (?, ?, ?, 'ai')",
        [userId, fund.fund_code, reason],
        function (err) {
          if (err) reject(err);
          else {
            if (this.changes > 0) inserted.push(fund.fund_code);
            resolve();
          }
        });
    });
  }
  return { inserted, removed: removedCount, kept: inserted.length, total: candidates.length, universe: universe.length };
}

// 新基金入库 funds 并拉全量历史净值（观察池/信号/交易都依赖 fund_nav）
async function ensureFundWithNav(f) {
  const inFunds = await new Promise((resolve) => {
    db.get('SELECT fund_code FROM funds WHERE fund_code = ?', [f.fund_code], (err, row) => resolve(err ? null : row));
  });
  if (inFunds) {
    const navN = await new Promise((resolve) => {
      db.get('SELECT COUNT(*) n FROM fund_nav WHERE fund_code = ?', [f.fund_code], (err, row) => resolve(err ? 0 : (row ? row.n : 0)));
    });
    return navN;
  }
  // 粗类 → 细类映射（universe 只有 股票型/混合型/指数型/QDII 四大类）
  let ft = '混合型-偏股';
  if (f.fund_type === '股票型') ft = '股票型';
  else if (f.fund_type === '指数型') ft = '指数型-股票';
  else if (f.fund_type === 'QDII') ft = 'QDII-普通股票';
  else if (/新能源|白酒|能源|科技|军工|医药|半导体|芯片|数字|人工智能|互联网/.test(f.fund_name || '')) ft = '混合型-偏股';
  else ft = '混合型-灵活';
  await new Promise((resolve, reject) => {
    db.run('INSERT INTO funds (fund_code, fund_name, fund_type) VALUES (?, ?, ?)', [f.fund_code, f.fund_name, ft], (err) => err ? reject(err) : resolve());
  });
  try {
    const fetcher = new FundDataFetcher();
    const navList = await fetcher.getNavHistoryAll(f.fund_code, '', '', 400);
    if (navList.length) await fetcher.saveNavData(navList);
    fetcher.close();
    console.log(`[全市场选基] 新基金入库+历史净值: ${f.fund_code} ${f.fund_name}（${ft}）共 ${navList.length} 条`);
    return navList.length;
  } catch (e) {
    console.error(`[全市场选基] ${f.fund_code} 净值拉取失败: ${e.message}`);
    return 0;
  }
}

// 时间/交易日函数已抽到 utils/time.js（唯一出处）；节假日表由该模块读 engine/holidays.json

// SQLite CURRENT_TIMESTAMP 存 UTC（无时区标记）→ 转本地时间串（YYYY-MM-DD HH:mm:ss）
function utcToLocalStr(utcStr) {
  try {
    const d = new Date(String(utcStr).replace(' ', 'T') + 'Z');
    if (isNaN(d.getTime())) return utcStr;
    const p = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
  } catch {
    return utcStr;
  }
}

// 判断 UTC 时间字符串是否属于今天（本地时区）
function isSameLocalDay(utcStr) {
  try {
    const d = new Date(utcStr.replace(' ', 'T') + 'Z');
    return getLocalDateStr(d) === getLocalDateStr(new Date());
  } catch {
    return false;
  }
}

// 保存某用户当日账户快照（真实数据，写入 portfolio_daily）
// 守卫：仅当“当日净值已公布”（fund_nav 最新净值日==今天）才写快照；
// 否则（盘中/净值未公布/非交易日）不写，避免用 T-1 净值产生伪确认盈亏。
async function saveDailySnapshot(userId) {
  const date = getLocalDateStr();
  // 守卫：仅当该用户全部持仓基金的当日净值均已公布才写快照；
  // 任一持仓基金当日净值未公布（陆续公布中）→ 不写，避免用 T-1 净值产生伪确认盈亏。
  const holdingCodes = await new Promise((resolve, reject) => {
    db.all('SELECT DISTINCT fund_code FROM holdings WHERE user_id = ?', [userId], (err, rows) => err ? reject(err) : resolve((rows || []).map(r => r.fund_code)));
  });
  if (holdingCodes.length === 0) return null; // 无持仓不写（今日盈亏由前端按空持仓处理为 0）
  for (const code of holdingCodes) {
    // T+1：当日买入的持仓当日按成本计市值（无收益），不依赖当日净值 → 跳过净值检查
    const lastBuy = await new Promise((resolve, reject) => {
      db.get("SELECT transaction_date FROM transactions WHERE user_id = ? AND fund_code = ? AND transaction_type = 'BUY' ORDER BY transaction_date DESC LIMIT 1",
        [userId, code], (err, row) => err ? reject(err) : resolve(row));
    });
    const pendingBuy = !!lastBuy && isSameLocalDay(lastBuy.transaction_date);
    if (pendingBuy) continue;
    const nav = await new Promise((resolve, reject) => {
      db.get('SELECT nav_date FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1', [code], (err, row) => err ? reject(err) : resolve(row));
    });
    if (!nav || nav.nav_date !== date) return null;
  }
  const portfolio = await getUserPortfolio(userId);
  let marketValue = 0;
  let todayPnl = 0;

  for (const [code, h] of Object.entries(portfolio.holdings)) {
    const navRow = await new Promise((resolve, reject) => {
      db.get('SELECT unit_nav, daily_return FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1', [code], (err, row) => {
        if (err) reject(err); else resolve(row);
      });
    });
    if (!navRow || !navRow.unit_nav) continue;

    // T+1 规则：当日买入的持仓当日无收益 → 市值按成本计（不计浮盈）
    const lastBuy = await new Promise((resolve, reject) => {
      db.get("SELECT transaction_date FROM transactions WHERE user_id = ? AND fund_code = ? AND transaction_type = 'BUY' ORDER BY transaction_date DESC LIMIT 1",
        [userId, code], (err, row) => err ? reject(err) : resolve(row));
    });
    const pendingBuy = !!lastBuy && isSameLocalDay(lastBuy.transaction_date);
    const mv = pendingBuy ? h.total_cost : h.shares * navRow.unit_nav;
    marketValue += mv;
    if (!pendingBuy) {
      todayPnl += mv * (navRow.daily_return || 0) / 100;
    }
  }

  const cash = portfolio.current_capital;
  const total = cash + marketValue;

  // 当日盈亏优先用与昨日总资产的差值（更准确），首日无昨日数据则用当日计算值
  const prev = await new Promise((resolve, reject) => {
    db.get('SELECT total_assets FROM portfolio_daily WHERE user_id = ? AND date < ? ORDER BY date DESC LIMIT 1', [userId, date], (err, row) => err ? reject(err) : resolve(row));
  });
  const dailyPnl = prev ? total - prev.total_assets : todayPnl;

  await new Promise((resolve, reject) => {
    db.run(`INSERT INTO portfolio_daily (user_id, date, total_assets, daily_pnl, cash, market_value) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET total_assets=excluded.total_assets, daily_pnl=excluded.daily_pnl, cash=excluded.cash, market_value=excluded.market_value`,
      [userId, date, total, dailyPnl, cash, marketValue], err => err ? reject(err) : resolve());
  });

  return { date, total, dailyPnl };
}

// AI分析状态
let aiAnalysisStatus = {
  status: 'idle',
  lastAnalysis: null,
  nextAnalysis: null,
  progress: 0,
  currentPhase: ''
};

// AI分析结果存储
let aiAnalysisResults = {};

// 获取用户持仓（从数据库）
function getUserPortfolio(userId) {
  return new Promise((resolve, reject) => {
    const portfolio = {
      initial_capital: userConfigs[userId]?.initial_capital || 100000,
      current_capital: userConfigs[userId]?.initial_capital || 100000,
      holdings: {},
      transactions: []
    };
    
    // 已实现盈亏（卖出净额-卖出成本，含赎回费影响），先取账本再算现金
    db.all('SELECT SUM(amount) AS total FROM realized_pnl WHERE user_id = ?', [userId], (errPnl, pnlRows) => {
      if (errPnl) {
        reject(errPnl);
        return;
      }
      const realizedTotal = (pnlRows && pnlRows[0] && pnlRows[0].total) || 0;
      portfolio.realized_pnl = realizedTotal;

      // 获取持仓
      db.all('SELECT * FROM holdings WHERE user_id = ?', [userId], (err, holdings) => {
        if (err) {
          reject(err);
          return;
        }

        holdings.forEach(h => {
          portfolio.holdings[h.fund_code] = {
            shares: h.shares,
            cost: h.cost_price,
            total_cost: h.total_cost
          };
          portfolio.current_capital -= h.total_cost;
        });
        // 现金 = 初始资金 - 持仓成本 + 已实现盈亏（卖出时已扣赎回费与价差）
        portfolio.current_capital += realizedTotal;

        // 获取交易记录
        db.all('SELECT * FROM transactions WHERE user_id = ? ORDER BY transaction_date DESC', [userId], (err, transactions) => {
          if (err) {
            reject(err);
            return;
          }

          portfolio.transactions = transactions;
          resolve(portfolio);
        });
      });
    });
  });
}

// 保存交易记录到数据库
function saveTransaction(userId, transaction) {
  return new Promise((resolve, reject) => {
    const sql = `INSERT INTO transactions (user_id, fund_code, transaction_type, amount, price, shares, fees, reason, remaining_shares) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, CASE WHEN ? = 'BUY' THEN ? ELSE NULL END)`;
    
    db.run(sql, [
      userId,
      transaction.fund_code,
      transaction.action,
      transaction.amount,
      transaction.price,
      transaction.shares,
      transaction.fees || 0,
      transaction.reason,
      transaction.action,
      transaction.shares
    ], function(err) {
      if (err) {
        reject(err);
      } else {
        resolve(this.lastID);
      }
    });
  });
}

// 更新持仓到数据库
function updateHolding(userId, fundCode, shares, costPrice, totalCost) {
  return new Promise((resolve, reject) => {
    const sql = `INSERT OR REPLACE INTO holdings (user_id, fund_code, shares, cost_price, total_cost, updated_at) 
                 VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)`;
    
    db.run(sql, [userId, fundCode, shares, costPrice, totalCost], function(err) {
      if (err) {
        reject(err);
      } else {
        resolve();
      }
    });
  });
}

// 获取AI分析结果（从数据库）
function getAnalysisResults(userId) {
  return new Promise((resolve, reject) => {
    db.all('SELECT * FROM ai_analysis WHERE user_id = ? ORDER BY analysis_time DESC', [userId], (err, rows) => {
      if (err) {
        reject(err);
        return;
      }
      
      const results = {};
      rows.forEach(row => {
        results[row.fund_code] = {
          decision: row.decision,
          confidence: row.confidence,
          entry_price: row.entry_price,
          target_price: row.target_price,
          stop_loss: row.stop_loss,
          analysis_time: row.analysis_time
        };
      });
      
      resolve(results);
    });
  });
}

// 保存AI分析结果到数据库
function saveAnalysisResult(userId, fundCode, result) {
  return new Promise((resolve, reject) => {
    const sql = `INSERT INTO ai_analysis (user_id, fund_code, decision, confidence, entry_price, target_price, stop_loss) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)`;
    
    db.run(sql, [
      userId,
      fundCode,
      result.decision,
      result.confidence,
      result.entry_price,
      result.target_price,
      result.stop_loss
    ], function(err) {
      if (err) {
        reject(err);
      } else {
        resolve(this.lastID);
      }
    });
  });
}

// 触发AI分析
app.post('/api/ai/analyze', async (req, res) => {
  try {
    let { fund_codes, user_id } = req.body;
    const userId = user_id || currentUser;

    if (!userConfigs[userId]) {
      return res.status(404).json({ error: '用户不存在' });
    }

    // 候选池 = 观察池：未指定或传空时，取该用户的观察池代码
    if (!fund_codes || !Array.isArray(fund_codes) || fund_codes.length === 0) {
      fund_codes = await getUserWatchlistCodes(userId);
    }

    if (fund_codes.length === 0) {
      return res.json({
        message: '观察池为空，请先在基金库中添加自选基金',
        results: {},
        trades: []
      });
    }

    // 更新分析状态
    aiAnalysisStatus.status = 'running';
    aiAnalysisStatus.progress = 0;
    aiAnalysisStatus.currentPhase = '开始分析...';

    // 基于真实信号分析观察池中的每只基金
    const analysisResults = {};
    const signals = {};

    for (let i = 0; i < fund_codes.length; i++) {
      const code = fund_codes[i];
      aiAnalysisStatus.progress = Math.round(((i + 1) / fund_codes.length) * 100);
      aiAnalysisStatus.currentPhase = `分析 ${code}...`;

      const sig = await getFundSignal(code);
      signals[code] = sig;

      if (!sig || !sig.signal || sig.latest_nav == null) {
        analysisResults[code] = {
          decision: 'HOLD',
          confidence: '低',
          entry_price: 0,
          target_price: 0,
          stop_loss: 0,
          analysis_time: new Date().toISOString(),
          signal_label: '数据不足',
          signal_reason: '暂无足够净值数据，无法分析',
          change_5d: null,
          change_20d: null,
          drawdown_60d: null,
          above_ma20: null
        };
        await saveAnalysisResult(userId, code, analysisResults[code]);
        continue;
      }

      const action = sig.signal.action;
      const entry = sig.latest_nav;
      analysisResults[code] = {
        decision: (action === 'buy' || action === 'add') ? 'BUY' : 'HOLD',
        confidence: action === 'buy' ? '高' : (action === 'add' ? '中' : '低'),
        entry_price: entry,
        target_price: Number((entry * 1.1).toFixed(4)),
        stop_loss: Number((entry * 0.95).toFixed(4)),
        analysis_time: new Date().toISOString(),
        signal_label: sig.signal.label,
        signal_reason: sig.signal.reason,
        change_5d: sig.change_5d,
        change_20d: sig.change_20d,
        drawdown_60d: sig.drawdown_60d,
        above_ma20: sig.above_ma20,
        nav_date: sig.nav_date,
        daily_return: sig.daily_return
      };
      await saveAnalysisResult(userId, code, analysisResults[code]);
    }

    // 更新状态
    aiAnalysisStatus.status = 'completed';
    aiAnalysisStatus.lastAnalysis = new Date().toISOString();
    aiAnalysisStatus.progress = 100;
    aiAnalysisStatus.currentPhase = '分析完成';
    aiAnalysisResults = analysisResults;

    // 只出建议供查看，系统不执行任何交易
    const suggestions = [];
    const portfolio = await getUserPortfolio(userId);

    for (const [code, result] of Object.entries(analysisResults)) {
      if (result.decision !== 'BUY') continue;
      const sig = signals[code];
      if (!sig || sig.latest_nav == null || sig.latest_nav <= 0) continue;

      const action = sig.signal.action;
      // 分批建仓(强信号)建议20%仓位，逢低加仓/轻仓试探建议10%
      const buyRatio = action === 'buy' ? 0.2 : 0.1;
      const suggestAmount = Math.round(portfolio.current_capital * buyRatio);
      result.suggest_amount = suggestAmount;
      suggestions.push({
        fund_code: code,
        signal: action,
        amount: suggestAmount,
        reason: sig.signal.reason
      });
      console.log(`AI分析建议买入（未执行）: ${code}（${action}）, 建议金额: ¥${suggestAmount}`);
    }

    const suggestCodes = suggestions.map(s => s.fund_code);
    res.json({
      message: suggestions.length > 0
        ? `分析完成：观察池 ${fund_codes.length} 只中 ${suggestions.length} 只出现入场信号（${suggestCodes.join('、')}），仅供查看参考，系统不执行交易`
        : `分析完成：观察池 ${fund_codes.length} 只均无入场信号，建议继续观望`,
      results: analysisResults,
      suggestions: suggestions,
      portfolio: {
        current_capital: portfolio.current_capital,
        holdings: portfolio.holdings
      },
      analysis_time: aiAnalysisStatus.lastAnalysis
    });
    
  } catch (error) {
    aiAnalysisStatus.status = 'error';
    aiAnalysisStatus.currentPhase = '分析失败: ' + error.message;
    res.status(500).json({ error: error.message });
  }
});

// AI 按当前用户性格自主选基进观察池（只读系统：只影响观察池，不涉及任何交易）
app.post('/api/ai/discover-watchlist', async (req, res) => {
  try {
    const userId = (req.body && req.body.user_id) || currentUser;
    if (!userConfigs[userId]) return res.status(404).json({ error: '用户不存在' });
    const result = await aiDiscoverWatchlist(userId);
    const list = await getWatchlist(userId);
    res.json({
      message: `AI已按${userConfigs[userId].style}维护观察池：新增 ${result.inserted.length} 只，自动调整 ${result.removed} 只`,
      inserted: result.inserted,
      removed: result.removed,
      watchlist: list
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 启动时为所有用户按性格自动选基（AI 自主维护观察池，幂等只补充）
async function autoDiscoverOnStartup() {
  try {
    for (const userId of Object.keys(userConfigs)) {
      const result = await aiDiscoverWatchlist(userId);
      if (result.inserted.length > 0) {
        console.log(`[AI自动选基] ${userConfigs[userId].name}（${userConfigs[userId].style}）新增观察: ${result.inserted.join(', ')}`);
      } else {
        console.log(`[AI自动选基] ${userConfigs[userId].name}（${userConfigs[userId].style}）观察池已是最新，无需补充`);
      }
    }
  } catch (e) {
    console.error('[AI自动选基] 启动执行失败:', e.message);
  }
}

// /api/ai/status 已抽到 routes/system.js
// /api/ai/results 已抽到 routes/system.js
// /api/ai/portfolio + /api/ai/compare + /api/ai/transactions 已抽到 routes/ai.js
// 单基金每日收益明细：日期 / 当日涨幅 / 当日持有份额 / 当日盈亏金额（T+1：买入当日无收益）
// /api/ai/fund-daily-pnl 已抽到 routes/readonly.js
// 获取AI交易记录
app.get('/api/ai/transactions', async (req, res) => {
  try {
    const userId = req.query.user_id || currentUser;
    const portfolio = await getUserPortfolio(userId);
    const txs = portfolio.transactions || [];
    // 附带真实基金名称（JOIN funds，取代前端硬编码映射）
    const enriched = [];
    for (const tx of txs) {
      const fund = await new Promise((resolve) => {
        db.get('SELECT fund_name FROM funds WHERE fund_code = ?', [tx.fund_code], (err, row) => resolve(err ? null : row));
      });
      enriched.push({ ...tx, fund_name: fund ? fund.fund_name : tx.fund_code });
    }
    // 待确认订单（T+1：SUBMITTED，20:00 按 trade_date 官方净值落账）
    const pendingRows = await new Promise((resolve, reject) => {
      db.all("SELECT id, fund_code, order_type, amount, shares, price, fee, status, order_date, trade_date, reason FROM orders WHERE user_id = ? AND status = 'SUBMITTED' ORDER BY id DESC", [userId], (err, rows) => err ? reject(err) : resolve(rows || []));
    });
    const pending = [];
    for (const p of pendingRows) {
      const fund = await new Promise((resolve) => {
        db.get('SELECT fund_name FROM funds WHERE fund_code = ?', [p.fund_code], (err, row) => resolve(err ? null : row));
      });
      pending.push({ ...p, fund_name: fund ? fund.fund_name : p.fund_code });
    }
    res.json({ list: enriched, pending });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// /api/ai/daily 已抽到 routes/readonly.js
// 用户管理API

// 获取所有用户列表
// ============ P0-1 新增 API：订单/审计/调度状态 ============
app.post('/api/scheduler/run', async (req, res) => {
  // 仅本机调试/测试用：手动触发周期任务（设计文档 §7）
  const type = (req.query.type || req.body.type || 'close').toLowerCase();
  const allowed = ['close', 'realtime', 'pre_close', 'confirm', 'weekly', 'monthly'];
  if (!allowed.includes(type)) {
    return res.status(400).json({ error: 'type 仅支持: ' + allowed.join(',') });
  }
  try {
    if (type === 'weekly') {
      // 手动触发周任务：评分更新 + 再平衡 + 换仓 + 周报（交易步骤受交易时段守卫；盘外触发跳过交易仅生成报告）
      await computeFundProfiles();
      const results = [];
      for (const userId of Object.keys(userConfigs)) {
        const cfg = await getRiskParams(userId);
        let rb = null, sw = null;
        try { rb = await rebalanceCheck(userId); } catch (e) { rb = 'SKIP:' + e.message; }
        try { sw = await switchFunds(userId); } catch (e) { sw = 'SKIP:' + e.message; }
        await generateReport(userId, 'weekly');
        results.push({ userId, rebalance: rb, switch: sw });
      }
      return res.json({ ok: true, type, results });
    }
    if (type === 'monthly') {
      // 手动触发月任务：归因 + 压力测试 + 月报 + 分红同步
      const results = [];
      for (const userId of Object.keys(userConfigs)) {
        const attr = await performanceAttribution(userId);
        await generatePressureReport(userId);
        await generateReport(userId, 'monthly');
        results.push({ userId, attribution: attr });
      }
      return res.json({ ok: true, type, results });
    }
    if (type === 'confirm') {
      const r = await confirmPendingOrders({ db, saveTransaction, updateHolding, audit });
      res.json({ ok: true, type, confirmed: r.confirmed, errors: r.errors });
    } else {
      const started = new Date().toISOString();
      await performAnalysis(type);
      const finished = new Date().toISOString();
      db.run(`INSERT INTO scheduler_runs (run_type, started_at, finished_at, status, summary) VALUES (?, ?, ?, 'done', ?)`,
        [type, started, finished, 'manual trigger'], (err) => { if (err) console.error('scheduler_runs 写入失败:', err.message); });
      res.json({ ok: true, type, started, finished });
    }
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

// /api/audit 已抽到 routes/readonly.js

// /api/ai/stream 已抽到 routes/system.js
// /api/scheduler/status 已抽到 routes/system.js
// ===== AI 经营成绩单（用户通过数据看 AI 决策质量）=====
// /api/ai/stats + /api/ai/activity 已抽到 routes/readonly.js
// 用户管理API
// ===== 账户级每日收益明细（跨基金按日贡献；账户快照对照含费口径）=====
// /api/ai/daily-pnl 已抽到 routes/readonly.js
// 账户累计收益率 vs 沪深300 基准（AI 操盘相对指数表现）
// /api/ai/performance-vs-benchmark 已抽到 routes/readonly.js
// /api/ai/fund-fees 已抽到 routes/readonly.js
// ===== AI 市场热点关注与分析（主题词聚类全市场 → 热点板块 + AI 点评 + 观察池关联）=====
const HOTSPOT_THEMES = [
  { key: '医药/医疗', kws: ['医药', '医疗', '生物', '健康', '创新药', '疫苗'] },
  { key: 'AI/科技', kws: ['人工智能', 'AI', '科技', '信息', '互联网', '软件', '计算机', '数字经济'] },
  { key: '白酒/消费', kws: ['白酒', '消费', '食品', '饮料', '啤酒', '乳业'] },
  { key: '半导体/芯片', kws: ['半导体', '芯片', '集成电路'] },
  { key: '新能源/光伏', kws: ['新能源', '光伏', '锂电', '电池', '碳中和', '储能', '风电'] },
  { key: '军工/国防', kws: ['军工', '国防', '航天', '卫星'] },
  { key: '港股/恒生', kws: ['港股', '恒生', '沪港深', 'H股'] },
  { key: '红利/价值', kws: ['红利', '价值', '低波', '沪深300'] },
  { key: '有色/资源', kws: ['有色', '资源', '矿业', '煤炭', '钢铁', '黄金'] },
  { key: '汽车/智能驾驶', kws: ['汽车', '智能驾驶', '自动驾驶'] },
  { key: '农业/养殖', kws: ['农业', '养殖', '农牧', '种业'] },
  { key: '地产/基建', kws: ['地产', '基建', '建筑', '建材'] },
  { key: '债券/固收', kws: ['债', '固收', '货币'] },
  { key: '量化/指数增强', kws: ['量化', '指数增强', '增强'] }
];

// 热点引擎：全市场基金按主题词聚类 → 板块平均日/周/月涨幅 → 热度分 + AI 点评（按用户性格）
async function buildHotspots(userId) {
  const all = (sql, params = []) => new Promise((resolve, reject) => db.all(sql, params, (e, r) => e ? reject(e) : resolve(r || [])));
  const rows = await all('SELECT fund_code, fund_name, day_return, r1w, r1m, scale FROM fund_universe');
  const agg = [];
  for (const t of HOTSPOT_THEMES) {
    const hits = rows.filter(r => t.kws.some(kw => (r.fund_name || '').includes(kw)) && r.day_return != null);
    if (hits.length < 3) continue;
    const n = hits.length;
    const avgDay = hits.reduce((s, r) => s + r.day_return, 0) / n;
    const wHits = hits.filter(r => r.r1w != null);
    const avgW = wHits.length ? wHits.reduce((s, r) => s + r.r1w, 0) / wHits.length : 0;
    const mHits = hits.filter(r => r.r1m != null);
    const avgM = mHits.length ? mHits.reduce((s, r) => s + r.r1m, 0) / mHits.length : 0;
    // 热度分：日动能为主、周动能辅
    const hotScore = +(avgDay * 1 + avgW * 0.4).toFixed(2);
    agg.push({ theme: t.key, count: n, avg_day: +avgDay.toFixed(2), avg_week: +avgW.toFixed(2), avg_month: +avgM.toFixed(2), hot_score: hotScore, kws: t.kws });
  }
  agg.sort((a, b) => b.hot_score - a.hot_score);
  const top = agg.slice(0, 6);

  // 观察池关联：热点板块内该用户已观察/持仓的基金
  const watchCodes = new Set((await all('SELECT fund_code FROM watchlist WHERE user_id = ?', [userId])).map(r => r.fund_code));
  const holdCodes = new Set((await all('SELECT fund_code FROM holdings WHERE user_id = ?', [userId])).map(r => r.fund_code));
  for (const h of top) {
    const related = rows.filter(r => h.kws.some(kw => (r.fund_name || '').includes(kw)) &&
      (watchCodes.has(r.fund_code) || holdCodes.has(r.fund_code)));
    h.related = related.map(r => ({ fund_code: r.fund_code, fund_name: r.fund_name, day_return: r.day_return, watched: watchCodes.has(r.fund_code), held: holdCodes.has(r.fund_code) })).slice(0, 5);
  }

  // AI 点评（规则引擎，按用户性格）
  const isAggressive = (userConfigs[userId] && userConfigs[userId].style === 'aggressive');
  const navDate = rows.filter(r => r.day_return != null).length ? '最新净值日' : '—';
  const hottest = top.find(h => h.hot_score > 0);
  let comment = '';
  let overall = '观望';
  if (!top.length) {
    comment = '当前基金库无明显热点板块，AI 维持防御，暂不追热点。';
    overall = '防御';
  } else if (hottest && hottest.avg_day >= 2.5) {
    overall = '热点爆发';
    comment = `${hottest.theme} 板块平均日涨幅 ${hottest.avg_day >= 0 ? '+' : ''}${hottest.avg_day}% 领涨全市场${isAggressive ? '，激进风格可关注相关基金轻仓介入，但注意不追高、等待回调企稳再加仓' : '，稳健风格暂不追高，等待回调确认后再评估'}`;
  } else if (hottest && hottest.avg_day >= 1) {
    overall = '热点启动';
    comment = `${hottest.theme} 板块 ${hottest.avg_day >= 0 ? '+' : ''}${hottest.avg_day}%（周 ${hottest.avg_week >= 0 ? '+' : ''}${hottest.avg_week}%）热点启动${isAggressive ? '，观察池相关基金若出现 BUY 信号可分批介入' : '，先观察持续性，确认不一日游再考虑'}`;
  } else if (hottest && hottest.avg_day > 0) {
    overall = '温和走强';
    comment = `${hottest.theme} 温和走强（日 ${hottest.avg_day >= 0 ? '+' : ''}${hottest.avg_day}%），暂未形成趋势性热点，AI 继续持有跟踪。`;
  } else {
    overall = '热点退潮';
    comment = '当日全市场板块普遍回调，无强势热点，AI 以控制回撤为主，不追跌。';
  }

  const result = { nav_date: navDate, generated_at: new Date().toISOString(), overall, comment, hotspots: top, user_style: isAggressive ? 'aggressive' : 'default' };
  return result;
}



// 市场行情概览：基准指数走势 + 市场温度 + 全市场基金涨跌统计
// /api/market/overview 已抽到 routes/readonly.js
app.get('/api/ai/hotspots', async (req, res) => {
  try {
    const userId = req.query.user_id || currentUser;
    if (!userConfigs[userId]) return res.status(404).json({ error: '用户不存在' });
    const data = await buildHotspots(userId);
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 用户管理API
// /api/users/* 路由已抽到 routes/users.js
// /api/analysis/logs + /api/analysis/latest 已抽到 routes/readonly.js
// 分析记录表（存档）
db.run(`CREATE TABLE IF NOT EXISTS analysis_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  analysis_type TEXT NOT NULL,
  fund_code TEXT NOT NULL,
  decision TEXT,
  confidence TEXT,
  entry_price REAL,
  target_price REAL,
  stop_loss REAL,
  current_nav REAL,
  daily_return REAL,
  estimated_close_return REAL,
  estimated_pnl REAL,
  signal_label TEXT,
  signal_reason TEXT,
  analysis_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (fund_code) REFERENCES funds (fund_code)
)`);

// 旧库迁移：analysis_logs 补 signal_label/signal_reason（热点分析记录用）
db.run("ALTER TABLE analysis_logs ADD COLUMN signal_label TEXT", (err) => {});
db.run("ALTER TABLE analysis_logs ADD COLUMN signal_reason TEXT", (err) => {});

// 定时任务配置
function scheduleAnalysis() {
  console.log('=== 定时分析任务配置 ===');
  console.log('');
  console.log('分析频率:');
  console.log('  - 实时分析: 每30分钟（交易时间内）');
  console.log('  - 收盘前分析: 每日14:30');
  console.log('  - 收盘分析: 每日15:00');
  console.log('');
  
  // 1. 实时分析 - 每30分钟
  scheduleRealtimeAnalysis();
  
  // 2. 收盘前分析 - 每日14:30
  schedulePreCloseAnalysis();
  
  // 3. 收盘分析 - 每日15:00
  scheduleCloseAnalysis();
  
  // 4. 盘后订单确认 - 每日20:00（T+1确认）
  schedulePostCloseConfirmation();

  // 5. 净值增量同步 - 每日21:30（天天基金当日净值公布后拉取）
  scheduleNavSync();
}

// 净值增量同步：拉取最近3个交易日的真实净值入库（startDate 需 YYYY-MM-DD 横线格式）
async function runNavSyncOnce() {
  try {
    const fetcher = new FundDataFetcher();
    const d = new Date();
    const sd = new Date(d); sd.setDate(sd.getDate() - 5);
    const startDate = sd.getFullYear() + '-' + String(sd.getMonth() + 1).padStart(2, '0') + '-' + String(sd.getDate()).padStart(2, '0');
    const funds = await new Promise((resolve, reject) => {
      fetcher.db.all('SELECT fund_code FROM funds ORDER BY fund_code', (err, rows) => err ? reject(err) : resolve(rows || []));
    });
    let inserted = 0;
    for (const f of funds) {
      try {
        const navList = await fetcher.getNavHistoryAll(f.fund_code, startDate, '', 3);
        if (navList.length > 0) inserted += await fetcher.saveNavData(navList);
      } catch (e) { console.error('[净值同步] ' + f.fund_code + ' 失败: ' + e.message); }
      await new Promise(r => setTimeout(r, 250));
    }
    fetcher.close();
    console.log('[净值同步] 完成，新入库 ' + inserted + ' 条（区间 ' + startDate + ' 起）');
    // 净值公布后生成当日确认快照（真实净值口径，供资产走势/每日盈亏图使用）
    for (const userId of Object.keys(userConfigs)) {
      try {
        const snapshot = await saveDailySnapshot(userId);
        if (snapshot) console.log(`[净值同步] ${userConfigs[userId].name} 当日快照已确认: ${snapshot.date} 总资产¥${snapshot.total.toFixed(2)} 当日盈亏¥${snapshot.dailyPnl.toFixed(2)}`);
      } catch (snapErr) {
        console.error(`[净值同步] 保存快照失败 ${userId}: ${snapErr.message}`);
      }
    }
  } catch (e) {
    console.error('[净值同步] 任务异常: ' + e.message);
  }
}

function scheduleNavSync() {
  const run = () => { runNavSyncOnce(); };
  const now = new Date();
  const target = new Date(now);
  target.setHours(21, 30, 0, 0);
  if (now > target) target.setDate(target.getDate() + 1);
  const delay = target.getTime() - now.getTime();
  setTimeout(() => {
    run();
    setInterval(run, 24 * 60 * 60 * 1000);
  }, delay);
  console.log('[净值同步] 每日 21:30 自动拉取当日净值（首次 ' + target.toLocaleString() + '）');
  // 22:30 补充同步：基金净值陆续公布（部分 22-23 点才出），确保当日确认快照完整
  const target2 = new Date(now);
  target2.setHours(22, 30, 0, 0);
  if (now > target2) target2.setDate(target2.getDate() + 1);
  const delay2 = target2.getTime() - now.getTime();
  setTimeout(() => {
    run();
    setInterval(run, 24 * 60 * 60 * 1000);
  }, delay2);
  console.log('[净值同步] 每日 22:30 补充同步（首次 ' + target2.toLocaleString() + '）');
  // 启动时立即补一次（防止停机期间数据缺失）
  setTimeout(run, 15 * 1000);
}

// 观察池周期扫描：AI 每日 09:35（盘前）+ 17:00（盘后）自动重扫全市场并更新观察池（真实扫描、持续动起来；后台执行不阻塞）
function scheduleWatchlistScan() {
  const runOnce = () => {
    autoDiscoverOnStartup().then(() => console.log('[观察池扫描] 本轮回合完成'));
  };
  const scheduleAt = (hour, minute) => {
    const now = new Date();
    const target = new Date(now);
    target.setHours(hour, minute, 0, 0);
    if (now > target) target.setDate(target.getDate() + 1);
    const delay = target.getTime() - now.getTime();
    setTimeout(() => {
      runOnce();
      setInterval(runOnce, 24 * 60 * 60 * 1000);
    }, delay);
    return target;
  };
  const t1 = scheduleAt(9, 35);
  const t2 = scheduleAt(17, 0);
  console.log('[观察池扫描] 每日 09:35 盘前 + 17:00 盘后自动重扫全市场（首次 ' + t1.toLocaleString() + ' / ' + t2.toLocaleString() + '）');
}

// 全市场基金库每日刷新（rankhandler 快照，供 AI 全市场选基与基金库展示；子进程不阻塞主服务）
function scheduleUniverseSync() {
  const run = () => {
    console.log('[全市场基金库] 开始刷新 fund_universe ...');
    const child = spawn(process.execPath, [path.join(__dirname, 'engine', 'sync-fund-universe.js')], {
      stdio: ['ignore', 'pipe', 'pipe']
    });
    child.stdout.on('data', d => process.stdout.write('[universe] ' + String(d)));
    child.stderr.on('data', d => process.stderr.write('[universe-err] ' + String(d)));
    child.on('exit', code => console.log('[全市场基金库] 刷新结束 code=' + code));
  };
  const now = new Date();
  const target = new Date(now);
  target.setHours(22, 5, 0, 0);
  if (now > target) target.setDate(target.getDate() + 1);
  const delay = target.getTime() - now.getTime();
  setTimeout(() => {
    run();
    setInterval(run, 24 * 60 * 60 * 1000);
  }, delay);
  console.log('[全市场基金库] 每日 22:05 自动刷新（首次 ' + target.toLocaleString() + '）');
}

// 实时分析 - 每30分钟
function scheduleRealtimeAnalysis() {
  const now = new Date();
  const hour = now.getHours();
  const minute = now.getMinutes();
  
  // 交易时间: 9:30-11:30, 13:00-15:00（且必须为交易日）
  const isTradingHour = (hour >= 9 && hour < 12) || (hour >= 13 && hour < 15);
  
  if (isTradingHour && isTradingDay(now)) {
    console.log('[实时分析] 当前在交易时间内，启动实时分析');
    
    // 计算到下一个30分钟间隔的时间
    const nextSlot = new Date(now);
    nextSlot.setMinutes(Math.ceil(minute / 30) * 30, 0, 0);
    
    if (nextSlot <= now) {
      nextSlot.setMinutes(nextSlot.getMinutes() + 30);
    }
    
    const delay = nextSlot.getTime() - now.getTime();
    console.log(`[实时分析] 下次分析: ${nextSlot.toLocaleTimeString('zh-CN')}`);
    
    let realtimeTimer = null;
    setTimeout(() => {
      performAnalysis('realtime', true);
      // 之后每30分钟执行一次；检测到收盘/盘外自动停掉，重排到下一交易日 9:30
      realtimeTimer = setInterval(() => {
        if (!isMarketOpenNow()) {
          console.log('[实时分析] 已收盘/非交易时段，停止半小时循环，重排到下一交易日 9:30');
          clearInterval(realtimeTimer);
          scheduleRealtimeAnalysis();
          return;
        }
        performAnalysis('realtime', true);
      }, 30 * 60 * 1000);
    }, delay);
  } else {
    // 非交易时间，计算到下一个交易时间的延迟
    let nextTradingTime = new Date(now);
    
    if (hour < 9 || (hour === 9 && minute < 30)) {
      nextTradingTime.setHours(9, 30, 0, 0);
    } else if (hour >= 15) {
      nextTradingTime = nextTradingDay(new Date(nextTradingTime.getTime() + 86400000));
      nextTradingTime.setHours(9, 30, 0, 0);
    } else if (hour >= 12) {
      nextTradingTime.setHours(13, 0, 0, 0);
    }
    // 非交易日（节假日）排到下一交易日 9:30
    if (!isTradingDay(nextTradingTime)) {
      nextTradingTime = nextTradingDay(nextTradingTime);
      nextTradingTime.setHours(9, 30, 0, 0);
    }
    
    const delay = nextTradingTime.getTime() - now.getTime();
    console.log(`[实时分析] 非交易时间，下次分析: ${nextTradingTime.toLocaleString('zh-CN')}`);
    
    setTimeout(() => {
      scheduleRealtimeAnalysis();
    }, delay);
  }
}

// 收盘前分析 - 每日14:30
function schedulePreCloseAnalysis() {
  const now = new Date();
  let targetTime = new Date(now);
  targetTime.setHours(14, 30, 0, 0);
  
  if (now > targetTime) {
    targetTime.setDate(targetTime.getDate() + 1);
  }
  // 非交易日顺延到下一交易日
  if (!isTradingDay(targetTime)) {
    targetTime = nextTradingDay(targetTime);
    targetTime.setHours(14, 30, 0, 0);
  }
  
  const delay = targetTime.getTime() - now.getTime();
  console.log(`[收盘前分析] 下次分析: ${targetTime.toLocaleString('zh-CN')}`);
  
  setTimeout(() => {
    performAnalysis('pre_close', true);
    // 每个交易日执行一次
    setInterval(() => performAnalysis('pre_close', true), 24 * 60 * 60 * 1000);
  }, delay);
}

// 收盘分析 - 每日15:00
function scheduleCloseAnalysis() {
  const now = new Date();
  let targetTime = new Date(now);
  targetTime.setHours(15, 0, 0, 0);
  
  if (now > targetTime) {
    targetTime.setDate(targetTime.getDate() + 1);
  }
  // 非交易日顺延到下一交易日
  if (!isTradingDay(targetTime)) {
    targetTime = nextTradingDay(targetTime);
    targetTime.setHours(15, 0, 0, 0);
  }
  
  const delay = targetTime.getTime() - now.getTime();
  console.log(`[收盘分析] 下次分析: ${targetTime.toLocaleString('zh-CN')}`);
  
  setTimeout(() => {
    performAnalysis('close', true);
    // 每个交易日执行一次
    setInterval(() => performAnalysis('close', true), 24 * 60 * 60 * 1000);
  }, delay);
}

// 执行分析
async function performAnalysis(analysisType, auto = false) {
  const typeNames = {
    'realtime': '实时分析',
    'pre_close': '收盘前分析',
    'close': '收盘分析'
  };
  
  // realtime 半小时分析双保险：非交易时段（周末/节假日/收盘后）直接跳过，不扫描/不选基/不下单
  if (analysisType === 'realtime' && auto && !isMarketOpenNow()) {
    console.log(`[实时分析] 非交易时段，跳过本次半小时分析`);
    return;
  }
  // pre_close/close 是交易日收盘任务：非交易日（周末/节假日）直接跳过，不生成空日报/不写快照
  if ((analysisType === 'pre_close' || analysisType === 'close') && auto && !isTradingDay()) {
    console.log(`[${analysisType}] 非交易日（周末/节假日），跳过`);
    return;
  }
  logAi('phase', { phase: 'start', message: `${typeNames[analysisType]}开始` });
  console.log(`\n=== ${typeNames[analysisType]}开始 ===`);
  console.log(`时间: ${new Date().toLocaleString('zh-CN')}`);
  
  try {
    for (const userId of Object.keys(userConfigs)) {
      // AI 先按性格自主刷新观察池（幂等补充，观察池=AI选股池，AI 自主维护）
      try {
        const discover = await aiDiscoverWatchlist(userId);
        if (discover.inserted.length > 0) {
          console.log(`[AI自动选基] ${userConfigs[userId].name} 新增观察: ${discover.inserted.join(', ')}`);
          logAi('discover', { user: userConfigs[userId].name, codes: discover.inserted, message: `🔍 AI 自主选基新增观察: ${discover.inserted.join(', ')}` });
        }
      } catch (e) {
        console.error(`[AI自动选基] ${userId} 刷新失败:`, e.message);
      }

      // 定时分析同样只观察「观察池」中的标的（观察池 = AI 选股池）
      const fundList = await getUserWatchlistCodes(userId);
      
      console.log(`\n用户: ${userConfigs[userId].name}`);
      if (fundList.length === 0) {
        console.log('观察池为空，无可分析的观察标的');
        continue;
      }
      console.log(`分析观察池: ${fundList.join(', ')}`);
      logAi('watchlist', { user: (userConfigs[userId]||{}).name || userId, count: fundList.length, message: `${(userConfigs[userId]||{}).name||userId} 开始分析观察池 ${fundList.length} 只` });
      
      // 获取当前持仓
      const portfolio = await getUserPortfolio(userId);
      
      // 分析观察池中的每只基金（真实信号）
      for (const fundCode of fundList) {
        const sig = await getFundSignal(fundCode);
        
        const currentNav = sig && sig.latest_nav != null ? sig.latest_nav : 0;
        const dailyReturn = sig && sig.daily_return != null ? sig.daily_return : 0;
        // ===== P1：数据质量校验（净值突变 >±10% 记录并跳过决策，不猜数）=====
        if (currentNav > 0 && !checkDataQuality(fundCode, sig && sig.nav_date, dailyReturn)) {
          console.log(`  → ${fundCode} 净值异动已标记，跳过本轮决策`);
          continue;
        }
        const action = sig && sig.signal ? sig.signal.action : 'wait';
        
        // 决策来自真实信号：分批建仓/逢低加仓 → BUY，其余 → 观察（HOLD）
        const decision = (action === 'buy' || action === 'add') ? 'BUY' : 'HOLD';
        const confidence = action === 'buy' ? '高' : (action === 'add' ? '中' : '低');
        logAi('signal', { user: (userConfigs[userId]||{}).name || userId, code: fundCode, action, decision, confidence, nav: currentNav, dailyReturn: dailyReturn.toFixed(2), message: `${fundCode} 信号=${action}（置信度${confidence}） 日涨跌${dailyReturn.toFixed(2)}% → ${decision}` });
        
        // 预估收盘涨跌幅用真实最新日涨跌，不再随机
        const estimatedCloseReturn = dailyReturn;
        const holding = portfolio.holdings[fundCode];
        const estimatedPnl = holding ? (holding.shares * currentNav * dailyReturn / 100).toFixed(2) : 0;
        
        // ===== P0-2：风控校验（BUY 下单前：回撤熔断/集中度/总仓位）=====
        if (auto && (action === 'buy' || action === 'add') && currentNav > 0) {
          try {
            const userCfg = await getRiskParams(userId);
            const holding2 = portfolio.holdings[fundCode];
            const hasHolding2 = !!holding2 && holding2.shares > 0;
            // 防重复下单：已有未确认（CREATED/SUBMITTED）买单则跳过
            const pendingBuy = await new Promise((resolve) => {
              db.get("SELECT COUNT(*) c FROM orders WHERE user_id=? AND fund_code=? AND order_type='BUY' AND status IN ('CREATED','SUBMITTED')",
                [userId, fundCode], (err, row) => resolve(err ? 0 : (row ? row.c : 0)));
            });
            if (pendingBuy > 0) {
              console.log(`  → ${fundCode} 已有待确认买单，跳过重复下单`);
            } else {
              // 市场温度系数（frozen 0.5 / cold 0.8 / warm 1.1 / hot 1.2）调节建仓/加仓金额
              const tempRow2 = await new Promise((resolve) => {
                db.get('SELECT temperature FROM market_env ORDER BY date DESC LIMIT 1', [], (err, row) => resolve(err ? null : row));
              });
              const tempFactor2 = temperatureFactor(tempRow2 ? tempRow2.temperature : 'neutral');

              if (!hasHolding2) {
                // ===== 首笔建仓（未持有）：buy 分批建仓 20%，add 轻仓试探 10% =====
                const ratio2 = action === 'buy' ? (userCfg.buy_ratio || 0.2) : (userCfg.add_ratio || 0.1);
                const suggestAmount2 = Math.round(portfolio.current_capital * ratio2 * tempFactor2);
                if (suggestAmount2 >= 100) {
                  const rc = await checkRiskControls(userId, portfolio, 'BUY', fundCode, suggestAmount2, userCfg);
                  if (!rc.pass) {
                    logRiskEvent(userId, 'BUY_BLOCKED', fundCode, rc.reason, 'block');
                    console.log(`  → 风控拦截买入 ${fundCode}: ${rc.reason}`);
                    logAi('block', { user: (userConfigs[userId]||{}).name || userId, code: fundCode, message: `🚫 风控拦截 ${fundCode}: ${rc.reason}` });
                  } else {
                    const order = await orderEngine.createOrder({ db, audit }, {
                      userId, fundCode, orderType: 'BUY', amount: suggestAmount2, price: currentNav,
                      reason: `AI自动建仓：${sig.signal.label}（${sig.signal.reason}）`
                    });
                    console.log(`  → 生成建仓订单#${order.id} ${fundCode} ¥${suggestAmount2}（T+1确认）`);
                    logAi('order', { user: (userConfigs[userId]||{}).name || userId, code: fundCode, action: 'BUY', amount: suggestAmount2, orderId: order.id, message: `📈 建仓订单#${order.id} ${fundCode} ¥${suggestAmount2}` });
                  }
                } else {
                  console.log(`  → ${fundCode} 可用现金不足（¥${portfolio.current_capital}），跳过建仓`);
                }
              } else {
                // ===== 已持有 → 分批加仓（真实分批建仓：回调企稳信号下分批加仓）=====
                // 加仓节奏：距上次确认买入 >= add_cooldown_days 天才允许再加仓，避免越加越重；
                // 单基金总仓位上限（max_single_fund）由 checkRiskControls 兜底
                const lastBuyRow = await new Promise((resolve) => {
                  db.get("SELECT MAX(transaction_date) md FROM transactions WHERE user_id=? AND fund_code=? AND transaction_type='BUY'",
                    [userId, fundCode], (err, row) => resolve(err ? null : row));
                });
                const cooldown = userCfg.add_cooldown_days || 5;
                let daysSince = 9999;
                if (lastBuyRow && lastBuyRow.md) {
                  const lastD = new Date(utcToLocalStr(lastBuyRow.md).slice(0, 10) + 'T00:00:00');
                  const todayD = new Date(getLocalDateStr(new Date()) + 'T00:00:00');
                  daysSince = Math.round((todayD.getTime() - lastD.getTime()) / 86400000);
                }
                if (daysSince < cooldown) {
                  console.log(`  → ${fundCode} 距上次加仓 ${daysSince} 天 < 冷却期 ${cooldown} 天，暂不加仓（分批节奏）`);
                } else {
                  const addAmount = Math.round(portfolio.current_capital * (userCfg.add_ratio || 0.1) * tempFactor2);
                  if (addAmount >= 100) {
                    const rc = await checkRiskControls(userId, portfolio, 'BUY', fundCode, addAmount, userCfg);
                    if (!rc.pass) {
                      logRiskEvent(userId, 'BUY_BLOCKED', fundCode, rc.reason, 'block');
                      console.log(`  → 风控拦截加仓 ${fundCode}: ${rc.reason}`);
                    } else {
                      const order = await orderEngine.createOrder({ db, audit }, {
                        userId, fundCode, orderType: 'BUY', amount: addAmount, price: currentNav,
                        reason: `AI自动加仓（分批建仓）：${sig.signal.label}（${sig.signal.reason}）`
                      });
                      console.log(`  → 生成加仓订单#${order.id} ${fundCode} ¥${addAmount}（T+1确认，分批加仓）`);
                    }
                  } else {
                    console.log(`  → ${fundCode} 可用现金不足（¥${portfolio.current_capital}），跳过加仓`);
                  }
                }
              }
            }
          } catch (orderErr) {
            console.error(`生成订单失败 ${fundCode}:`, orderErr.message);
          }
        }

        // 计算目标价和止损价
        const targetPrice = currentNav ? (currentNav * 1.1).toFixed(4) : 0;
        const stopLoss = currentNav ? (currentNav * 0.95).toFixed(4) : 0;
        
        // 保存分析记录
        const sql = `INSERT INTO analysis_logs 
          (user_id, analysis_type, fund_code, decision, confidence, entry_price, target_price, stop_loss, current_nav, daily_return, estimated_close_return, estimated_pnl) 
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`;
        
        db.run(sql, [
          userId,
          analysisType,
          fundCode,
          decision,
          confidence,
          currentNav,
          targetPrice,
          stopLoss,
          currentNav,
          dailyReturn,
          parseFloat(estimatedCloseReturn),
          parseFloat(estimatedPnl)
        ], function(err) {
          if (err) {
            console.error(`保存分析记录失败: ${err.message}`);
          }
        });
        
        // ===== P1：研究笔记（决策依据/理由/指标，前端可读）=====
        if (currentNav > 0) {
          db.run('INSERT INTO research_notes (user_id, fund_code, analysis_type, signal, reason, metrics) VALUES (?, ?, ?, ?, ?, ?)',
            [userId, fundCode, analysisType, action, sig.signal.reason || decision,
             JSON.stringify({ nav: currentNav, daily: dailyReturn, change_20d: sig.change_20d, drawdown_60d: sig.drawdown_60d })], (err) => {
              if (err) console.error('研究笔记写入失败:', err.message);
            });
        }

        console.log(`  ${fundCode}: ${decision} (信号:${action}) 当前:¥${currentNav} 日涨跌:${dailyReturn}%`);
      }
    }
    
    // ===== P0-2：收盘时对全部持仓跑退场信号（止损/止盈/趋势/回撤）→ 生成 SELL 订单 =====
    if (analysisType === 'close' && auto) {
      for (const userId of Object.keys(userConfigs)) {
        try {
          const userCfg = await getRiskParams(userId);
          const pf = await getUserPortfolio(userId);
          for (const [fundCode, holding] of Object.entries(pf.holdings)) {
            if (!holding || holding.shares <= 0) continue;
            const exit = await buildExitSignal(userId, fundCode, holding, userCfg);
            if (exit.action === 'hold') {
              console.log(`  [退场] ${fundCode} 继续持有（${exit.label}）`);
              continue;
            }
            // 防重复减仓：趋势类 reduce 每 7 个自然日最多触发一次（止损清仓 sell 不受限）
            if (exit.action === 'reduce') {
              const recentSell = await new Promise((resolve) => {
                db.get("SELECT COUNT(*) c FROM orders WHERE user_id=? AND fund_code=? AND order_type='SELL' AND order_date >= date('now','-7 day')",
                  [userId, fundCode], (err, row) => resolve(err ? 0 : (row ? row.c : 0)));
              });
              if (recentSell > 0) {
                console.log(`  [退场] ${fundCode} 7日内已有减仓单，跳过重复减仓`);
                continue;
              }
            }
            const sellShares = Math.max(1, Math.round(holding.shares * (exit.ratio || 0.5)));
            const sig2 = await getFundSignal(fundCode);
            const nav2 = sig2 && sig2.latest_nav != null ? sig2.latest_nav : 0;
            if (nav2 <= 0) {
              console.log(`  [退场] ${fundCode} 净值缺失，跳过`);
              continue;
            }
            try {
              const order = await orderEngine.createOrder({ db, audit }, {
                userId, fundCode, orderType: 'SELL', amount: 0, shares: sellShares, price: nav2,
                reason: `AI自动退场：${exit.label}（${exit.reason}）`
              });
              console.log(`  → 生成卖出订单#${order.id} ${fundCode} ${sellShares}份（${exit.label}）`);
              logRiskEvent(userId, exit.action === 'sell' ? 'STOP_LOSS_SELL' : 'REDUCE', fundCode, exit.reason, exit.action);
            } catch (e) {
              console.error(`生成卖出订单失败 ${fundCode}:`, e.message);
            }
          }
        } catch (exitErr) {
          console.error(`[退场检查] ${userId} 失败:`, exitErr.message);
        }
      }
    }

    // 收盘后：AI 市场热点关注与分析（每用户独立点评，写 analysis_logs type=hotspot）
    if (analysisType === 'close') {
      for (const userId of Object.keys(userConfigs)) {
        try {
          const hp = await buildHotspots(userId);
          await new Promise((resolve) => {
            db.run('INSERT INTO analysis_logs (user_id, analysis_type, fund_code, decision, confidence, entry_price, target_price, stop_loss, analysis_time, current_nav, daily_return, estimated_close_return, estimated_pnl, signal_label, signal_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
              [userId, 'hotspot', 'HOTSPOT', hp.overall, hp.hot_score || 0, 0, 0, 0, new Date().toISOString(), 0, 0, 0, 0, hp.hottest_theme || (hp.hotspots[0] && hp.hotspots[0].theme) || '', hp.comment], (err) => resolve());
          });
          console.log(`[热点] ${userId} AI 热点分析：${hp.overall}（${hp.hotspots.map(h => h.theme + ' ' + h.avg_day + '%').slice(0, 3).join(' / ')}）${hp.comment.slice(0, 40)}`);
        } catch (hpErr) {
          console.error(`[热点] ${userId} 热点分析失败:`, hpErr.message);
        }
      }
    }

    // 收盘分析后保存当日账户快照（用于资产走势/每日盈亏真实图表）
    if (analysisType === 'close') {
      for (const userId of Object.keys(userConfigs)) {
        try {
          const snapshot = await saveDailySnapshot(userId);
          if (snapshot) console.log(`已保存 ${userConfigs[userId].name} 账户快照: ${snapshot.date} 总资产¥${snapshot.total.toFixed(2)} 当日盈亏¥${snapshot.dailyPnl.toFixed(2)}`);
        } catch (snapErr) {
          console.error(`保存账户快照失败: ${snapErr.message}`);
        }
      }
    }
    
    // ===== P0-3：基准指数更新 + 绩效计算 + 周报/月报 =====
    if (analysisType === 'close') {
      await fetchBenchmark();
      const todayStr = getLocalDateStr();
      const now = new Date();
      const dayOfWeek = now.getDay();
      const isLastTradingDayOfMonth = dayOfWeek === 5 && (now.getDate() + 7 > new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate());
      for (const userId of Object.keys(userConfigs)) {
        try {
          const perf = await computePerformance(userId, todayStr);
          console.log(`[绩效] ${userId} 总收益${perf.totalReturn.toFixed(2)}% 基准${perf.benchReturn.toFixed(2)}% 超额${perf.excessReturn.toFixed(2)}% 夏普${perf.sharpe.toFixed(2)}`);
          if (dayOfWeek === 5) {
            const rep = await generateReport(userId, 'weekly');
            console.log(`[报告] ${userId} 周报已生成（${rep.period}）`);
          }
          if (isLastTradingDayOfMonth) {
            const rep = await generateReport(userId, 'monthly');
            console.log(`[报告] ${userId} 月报已生成（${rep.period}）`);
          }
        } catch (perfErr) {
          console.error(`[绩效] ${userId} 计算失败:`, perfErr.message);
        }
      }
    }

    // ===== P1：评分/市场温度/分红/再平衡/换仓/归因/压力/复盘 =====
    if (analysisType === 'close') {
      const now = new Date();
      const dayOfWeek = now.getDay();
      const isLastTradingDayOfMonth = dayOfWeek === 5 && (now.getDate() + 7 > new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate());
      try { await computeMarketEnv(); } catch (e) { console.error('[市场温度] 失败:', e.message); }
      // 每周五更新基金评分画像
      if (dayOfWeek === 5) { try { await computeFundProfiles(); } catch (e) { console.error('[评分] 失败:', e.message); } }
      // 每月初同步分红记录
      if (now.getDate() <= 3) { try { await dividendAdjust(); } catch (e) { console.error('[分红] 失败:', e.message); } }
      for (const userId of Object.keys(userConfigs)) {
        try {
          const cfg = await getRiskParams(userId);
          // 再平衡（weekly 每周五 / monthly 月末）
          if ((cfg.rebalance_frequency === 'weekly' && dayOfWeek === 5) || (cfg.rebalance_frequency === 'monthly' && isLastTradingDayOfMonth)) {
            await rebalanceCheck(userId);
          }
          // 换仓评估（每周五）
          if (dayOfWeek === 5) { await switchFunds(userId); }
          // 业绩归因（月末）→ 追加到月报
          if (isLastTradingDayOfMonth) {
            try { const attr = await performanceAttribution(userId); if (attr) console.log(`[归因] ${userId} 配置贡献${attr.allocation}% 选基贡献${attr.selection}% 总超额${attr.totalExcess}%`); } catch (e) { console.error('[归因] 失败:', e.message); }
            try { await generatePressureReport(userId); console.log(`[压力] ${userId} 压力测试报告已生成`); } catch (e) { console.error('[压力] 失败:', e.message); }
          }
        } catch (p1Err) { console.error(`[P1] ${userId} 失败:`, p1Err.message); }
      }
      // 每日复盘（每日收盘后）
      try { await generateDailyRecap(); } catch (e) { console.error('[复盘] 失败:', e.message); }
    }

    console.log(`\n=== ${typeNames[analysisType]}完成 ===\n`);
    
  } catch (error) {
    console.error(`${typeNames[analysisType]}失败:`, error.message);
  }
}

// Vue Router history 模式 + 前端生产构建静态文件（与 server-production.js 一致）
app.use(history());
app.use(express.static(path.join(__dirname, 'frontend/dist')));

// 静态文件服务（放在API路由之后）
app.use(express.static('public'));

// 挂载 AI 核心路由（必须在 SPA fallback 之前）
app.use('/api/ai', require('./routes/ai')({ db, getUserPortfolio, getCurrentUser, getLocalDateStr, userConfigs }));

// 挂载系统/SSE 路由（必须在 SPA fallback 之前）
app.use('/api', require('./routes/system')({ aiAnalysisStatus, aiBus, isTradingDay, getAnalysisResults, getCurrentUser }));

// 挂载只读查询路由（必须在 SPA fallback 之前）
app.use('/api', require('./routes/readonly')({ db, getCurrentUser, getRiskParams }));

// 挂载用户路由（必须在 SPA fallback 之前）
app.use('/api/users', require('./routes/users')({
  db, userConfigs, getCurrentUser, setCurrentUser, getWatchlist, ensureFundWithNav
}));

// 其他请求兜底返回 Vue index.html
app.use((req, res) => {
  res.sendFile(path.join(__dirname, 'frontend/dist', 'index.html'));
});

// 统一错误处理中间件（必须最后挂）
app.use(errorHandler);

// 启动服务器
app.listen(PORT, () => {
  console.log(`基金模拟系统服务器运行在 http://localhost:${PORT}`);
  console.log('');
  console.log('=== 数据持久化说明 ===');
  console.log('- 交易记录已保存到SQLite数据库');
  console.log('- 持仓数据已保存到SQLite数据库');
  console.log('- 分析结果已保存到SQLite数据库');
  console.log('- 分析记录已保存到SQLite数据库（存档）');
  console.log('- 服务器重启后数据不会丢失');
  console.log('');
  
  // 启动定时任务
  scheduleAnalysis();
  scheduleUniverseSync();
  scheduleWatchlistScan();

  // 启动时确认跨交易日未确认订单（恢复场景）
  setTimeout(() => {
    confirmPendingOrders({ db, saveTransaction, updateHolding, audit }).then(r => {
      console.log(`[订单确认] 启动恢复确认 ${r.confirmed} 笔` + (r.errors.length ? `，错误 ${r.errors.length}` : ''));
    }).catch(e => console.error('[订单确认] 启动恢复失败:', e.message));
  }, 3000);

  // 启动时 AI 为所有用户按性格自动选基（观察池自主维护，无需用户操作）
  setTimeout(() => {
    autoDiscoverOnStartup();
  }, 2000);

  // 启动时保存一次当日账户快照（真实数据，供资产走势/每日盈亏图使用）
  setTimeout(async () => {
    for (const userId of Object.keys(userConfigs)) {
      try {
        const snapshot = await saveDailySnapshot(userId);
        if (snapshot) console.log(`已保存 ${userConfigs[userId].name} 启动快照: ${snapshot.date} 总资产¥${snapshot.total.toFixed(2)} 当日盈亏¥${snapshot.dailyPnl.toFixed(2)}`);
      } catch (err) {
        console.error(`保存启动快照失败: ${err.message}`);
      }
    }
  }, 1500);
});

// 优雅关闭
process.on('SIGINT', () => {
  console.log('服务器正在关闭...');
  db.close((err) => {
    if (err) {
      console.error('关闭数据库连接失败:', err.message);
    } else {
      console.log('数据库连接已关闭');
    }
    process.exit(0);
  });
});