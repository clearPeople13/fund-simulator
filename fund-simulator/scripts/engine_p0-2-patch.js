// P0-2 改造脚本：退场信号引擎 + 风控校验 + 性格画像补全
// 规格：fund/AI_FUND_OPERATIONS_DESIGN.md §2.2 §4.3 §4.5
const fs = require('fs');
const p = 'C:/Users/jiancent/WorkBuddy/fund/fund-simulator/server.js';
let s = fs.readFileSync(p, 'utf8');
const fail = (m) => { console.error('FAIL: ' + m); process.exit(1); };

// R1: 补建表（risk_events / performance_daily / reports / fund_profiles / research_notes）
{
  const anchor = "      UNIQUE(user_id, param_name)\n    )`);\n";
  if (!s.includes(anchor)) fail('R1 锚点未找到');
  const tables = `      UNIQUE(user_id, param_name)
    )\`);
    db.run(\`CREATE TABLE IF NOT EXISTS risk_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      event_type TEXT,
      fund_code TEXT,
      detail TEXT,
      action TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )\`);
    db.run(\`CREATE TABLE IF NOT EXISTS performance_daily (
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
    )\`);
    db.run(\`CREATE TABLE IF NOT EXISTS reports (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      report_type TEXT,
      period TEXT,
      content TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )\`);
    db.run(\`CREATE TABLE IF NOT EXISTS fund_profiles (
      fund_code TEXT PRIMARY KEY,
      volatility REAL,
      downside_risk REAL,
      style_label TEXT,
      score REAL,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )\`);
    db.run(\`CREATE TABLE IF NOT EXISTS research_notes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      fund_code TEXT NOT NULL,
      analysis_type TEXT,
      signal TEXT,
      reason TEXT,
      metrics TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )\`);
`;
  s = s.replace(anchor, tables);
}

// R2: userConfigs 补全性格画像（全参数驱动一切）
{
  const oldStart = "const userConfigs = {";
  const oldEnd = "// 当前活跃用户";
  const i1 = s.indexOf(oldStart);
  const i2 = s.indexOf(oldEnd);
  if (i1 < 0 || i2 < 0 || i2 <= i1) fail('R2 锚点未找到');
  const newConfigs = `const userConfigs = {
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

`;
  s = s.slice(0, i1) + newConfigs + s.slice(i2);
}

// R3: 新增函数：getRiskParams / 连续下跌计算 / buildExitSignal / checkRiskControls / getPortfolioDrawdown / logRiskEvent
{
  const anchor = "// 盘后订单确认任务：每日 20:00 确认前一日（含更早）SUBMITTED 订单（T+1 规则）";
  if (!s.includes(anchor)) fail('R3 锚点未找到');
  const fns = `// ============ P0-2 退场信号 + 风控引擎（规格 §2.2/§4.3/§4.5）============

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
        reason: \`亏损 \${pnlPct.toFixed(1)}% 触及止损线（-\${stopLossPct}%），\${name}为激进风格，连续下跌 \${consecDown} 日未确认恶化，先减 50% 控险\` };
    }
    return { action: 'sell', label: '清仓止损', ratio: 1,
      reason: \`亏损 \${pnlPct.toFixed(1)}% 触发止损线（-\${stopLossPct}%），\${name}按 \${exitStyle === 'timely' ? '及时' : '恶化确认'} 风格执行\` };
  }
  // 2) 止盈：盈利达止盈线
  if (pnlPct >= takeProfitPct) {
    if (exitStyle === 'timely') {
      return { action: 'reduce', label: '止盈减仓', ratio: 0.5,
        reason: \`盈利 \${pnlPct.toFixed(1)}% 达止盈线（+\${takeProfitPct}%），稳健风格锁定一半利润\` };
    }
    return { action: 'hold', label: '持有奔跑',
      reason: \`盈利 \${pnlPct.toFixed(1)}% 达止盈线，\${name}为激进风格，继续持有等趋势转空\` };
  }
  // 3) 趋势转空：近20日下跌 且 跌破20日线
  if (sig.change_20d != null && sig.change_20d < 0 && sig.above_ma20 === false) {
    if (exitStyle === 'patient' && consecDown < 2) {
      return { action: 'hold', label: '观察确认',
        reason: \`近20日 \${sig.change_20d.toFixed(1)}% 且跌破20日线，激进风格等待连续恶化确认\` };
    }
    return { action: 'reduce', label: '趋势转空减仓', ratio: 0.5,
      reason: \`近20日 \${sig.change_20d.toFixed(1)}% 且跌破20日线，趋势转空，减仓 50%\` };
  }
  // 4) 单基金回撤过大（距60日高点）
  if (sig.drawdown_60d != null && sig.drawdown_60d >= exitDrawdown) {
    return { action: 'reduce', label: '回撤过大减仓', ratio: 0.5,
      reason: \`距60日高点回撤 \${sig.drawdown_60d.toFixed(1)}% 超 \${exitDrawdown}% 阈值，减仓控制风险\` };
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
      return { pass: false, reason: \`组合回撤 \${dd.toFixed(1)}% 达熔断线（-\${maxDD}%），暂停新买入，仅允许减仓\` };
    }
    const maxSingle = (userCfg.max_single_fund || 0.2) * totalAssets;
    const curHoldingVal = portfolio.holdings[fundCode] ? (portfolio.holdings[fundCode].total_cost || 0) : 0;
    if (curHoldingVal + amount > maxSingle) {
      return { pass: false, reason: \`单基金仓位将超上限（≤\${(userCfg.max_single_fund * 100).toFixed(0)}%），当前+拟买超限\` };
    }
    const maxPos = (userCfg.max_position || 0.3) * totalAssets;
    const curPos = Object.values(portfolio.holdings).reduce((sum, h) => sum + (h.total_cost || 0), 0);
    if (curPos + amount > maxPos) {
      return { pass: false, reason: \`总仓位将超上限（≤\${(userCfg.max_position * 100).toFixed(0)}%），当前+拟买超限\` };
    }
  }
  return { pass: true, reason: '' };
}

// 记录风控事件（risk_events）
function logRiskEvent(userId, eventType, fundCode, detail, action) {
  db.run(\`INSERT INTO risk_events (user_id, event_type, fund_code, detail, action) VALUES (?, ?, ?, ?, ?)\`,
    [userId, eventType, fundCode || '', detail || '', action || ''], (err) => {
      if (err) console.error('风控事件写入失败:', err.message);
    });
  audit('risk-engine', 'RISK_EVENT', userId + ' ' + fundCode, { eventType, detail, action });
}

// 盘后订单确认任务：每日 20:00 确认前一日（含更早）SUBMITTED 订单（T+1 规则）`;
  s = s.replace(anchor, fns);
}

// R4: 收盘分析接入：持仓退场 → SELL 订单；BUY 前风控校验
{
  const anchor = "        // 收盘决策 → 生成真实订单（T 日下单，T+1 确认；不立即动持仓/现金）";
  if (!s.includes(anchor)) fail('R4 锚点未找到');
  const inject = `        // ===== P0-2：风控校验（BUY 下单前：回撤熔断/集中度/总仓位）=====
        if (analysisType === 'close' && (action === 'buy' || action === 'add') && currentNav > 0) {
          try {
            const userCfg = await getRiskParams(userId);
            const holding2 = portfolio.holdings[fundCode];
            const hasHolding2 = !!holding2 && holding2.shares > 0;
            if (!hasHolding2) {
              const ratio2 = action === 'buy' ? (userCfg.buy_ratio || 0.2) : (userCfg.add_ratio || 0.1);
              const suggestAmount2 = Math.round(portfolio.current_capital * ratio2);
              if (suggestAmount2 >= 100) {
                const rc = await checkRiskControls(userId, portfolio, 'BUY', fundCode, suggestAmount2, userCfg);
                if (!rc.pass) {
                  logRiskEvent(userId, 'BUY_BLOCKED', fundCode, rc.reason, 'block');
                  console.log(\`  → 风控拦截买入 \${fundCode}: \${rc.reason}\`);
                } else {
                  const order = await orderEngine.createOrder({ db, audit }, {
                    userId, fundCode, orderType: 'BUY', amount: suggestAmount2, price: currentNav,
                    reason: \`AI自动建仓：\${sig.signal.label}（\${sig.signal.reason}）\`
                  });
                  console.log(\`  → 生成买入订单#\${order.id} \${fundCode} ¥\${suggestAmount2}（T+1确认）\`);
                }
              } else {
                console.log(\`  → \${fundCode} 可用现金不足（¥\${portfolio.current_capital}），跳过下单\`);
              }
            }
          } catch (orderErr) {
            console.error(\`生成订单失败 \${fundCode}:\`, orderErr.message);
          }
        }

        // 收盘决策 → 生成真实订单（T 日下单，T+1 确认；不立即动持仓/现金）`;
  s = s.replace(anchor, inject);
}

// R5: 收盘阶段追加持仓退场检查（在"收盘分析后保存当日账户快照"之前）
{
  const anchor = "    // 收盘分析后保存当日账户快照（用于资产走势/每日盈亏真实图表）";
  if (!s.includes(anchor)) fail('R5 锚点未找到');
  const inject = `    // ===== P0-2：收盘时对全部持仓跑退场信号（止损/止盈/趋势/回撤）→ 生成 SELL 订单 =====
    if (analysisType === 'close') {
      for (const userId of Object.keys(userConfigs)) {
        try {
          const userCfg = await getRiskParams(userId);
          const pf = await getUserPortfolio(userId);
          for (const [fundCode, holding] of Object.entries(pf.holdings)) {
            if (!holding || holding.shares <= 0) continue;
            const exit = await buildExitSignal(userId, fundCode, holding, userCfg);
            if (exit.action === 'hold') {
              console.log(\`  [退场] \${fundCode} 继续持有（\${exit.label}）\`);
              continue;
            }
            const sellShares = Math.max(1, Math.round(holding.shares * (exit.ratio || 0.5)));
            const sig2 = await getFundSignal(fundCode);
            const nav2 = sig2 && sig2.latest_nav != null ? sig2.latest_nav : 0;
            if (nav2 <= 0) {
              console.log(\`  [退场] \${fundCode} 净值缺失，跳过\`);
              continue;
            }
            try {
              const order = await orderEngine.createOrder({ db, audit }, {
                userId, fundCode, orderType: 'SELL', amount: 0, shares: sellShares, price: nav2,
                reason: \`AI自动退场：\${exit.label}（\${exit.reason}）\`
              });
              console.log(\`  → 生成卖出订单#\${order.id} \${fundCode} \${sellShares}份（\${exit.label}）\`);
              logRiskEvent(userId, exit.action === 'sell' ? 'STOP_LOSS_SELL' : 'REDUCE', fundCode, exit.reason, exit.action);
            } catch (e) {
              console.error(\`生成卖出订单失败 \${fundCode}:\`, e.message);
            }
          }
        } catch (exitErr) {
          console.error(\`[退场检查] \${userId} 失败:\`, exitErr.message);
        }
      }
    }

    // 收盘分析后保存当日账户快照（用于资产走势/每日盈亏真实图表）`;
  s = s.replace(anchor, inject);
}

// R6: 新 API（risk/events、risk/params）
{
  const anchor = "app.get('/api/orders', (req, res) => {";
  if (!s.includes(anchor)) fail('R6 锚点未找到');
  const apis = `app.get('/api/risk/events', (req, res) => {
  const userId = req.query.user_id || currentUser;
  const limit = Math.min(parseInt(req.query.limit) || 50, 200);
  db.all('SELECT * FROM risk_events WHERE user_id = ? ORDER BY id DESC LIMIT ?', [userId, limit], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ events: rows });
  });
});

app.get('/api/risk/params/:user_id', async (req, res) => {
  try {
    const cfg = await getRiskParams(req.params.user_id);
    res.json({ user_id: req.params.user_id, params: cfg });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.get('/api/orders', (req, res) => {`;
  s = s.replace(anchor, apis);
}

fs.writeFileSync(p, s, 'utf8');
console.log('P0-2 patch 完成，新长度:', s.length);
