// P0-1 改造脚本：给 server.js 注入订单引擎/建表/审计/收盘下单/盘后确认/新API
const fs = require('fs');
const p = 'C:/Users/jiancent/WorkBuddy/fund/fund-simulator/server.js';
let s = fs.readFileSync(p, 'utf8');
const before = s;
const fail = (m) => { console.error('FAIL: ' + m); process.exit(1); };

// R1: require engine
{
  const old = "const history = require('connect-history-api-fallback');\n\nconst app = express();";
  if (!s.includes(old)) fail('R1 锚点未找到');
  s = s.replace(old, "const history = require('connect-history-api-fallback');\nconst orderEngine = require('./engine/order-engine');\nconst feeEngine = require('./engine/fee');\n\nconst app = express();");
}

// R2: 建表区追加（锚点：seedWatchlist 注释 + AI分析结果表）
{
  const anchor = "    // seedWatchlist();\n\n    // AI分析结果表";
  if (!s.includes(anchor)) fail('R2 锚点未找到');
  const tables = `    // P0-1 订单引擎相关表（规格: AI_FUND_OPERATIONS_DESIGN.md §5.2）
    db.run(\`CREATE TABLE IF NOT EXISTS orders (
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
      confirm_date TEXT,
      reason TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )\`);
    db.run(\`CREATE TABLE IF NOT EXISTS fund_fees (
      fund_code TEXT PRIMARY KEY,
      buy_fee_pct REAL, sell_fee_7d REAL, sell_fee_1y REAL, sell_fee_ge1y REAL,
      manage_fee_pct REAL, custody_fee_pct REAL, service_fee_pct REAL,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )\`);
    db.run(\`CREATE TABLE IF NOT EXISTS audit_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      actor TEXT,
      action TEXT,
      target TEXT,
      detail TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )\`);
    db.run(\`CREATE TABLE IF NOT EXISTS scheduler_runs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      run_type TEXT,
      started_at DATETIME,
      finished_at DATETIME,
      status TEXT,
      summary TEXT
    )\`);
    db.run(\`CREATE TABLE IF NOT EXISTS risk_params (
      user_id TEXT NOT NULL,
      param_name TEXT NOT NULL,
      param_value TEXT,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(user_id, param_name)
    )\`);

`;
  s = s.replace(anchor, tables + anchor);
}

// R3: audit + isTradingDay 函数（锚点：getUserWatchlistCodes 定义）
{
  const anchor = "function getUserWatchlistCodes(userId) {";
  if (!s.includes(anchor)) fail('R3 锚点未找到');
  const fns = `// 审计日志（全链路留痕）
function audit(actor, action, target, params) {
  let detail = '';
  try { detail = JSON.stringify(params || {}); } catch (e) {}
  db.run(\`INSERT INTO audit_logs (actor, action, target, detail) VALUES (?, ?, ?, ?)\`,
    [actor, action, String(target || ''), detail], (err) => {
      if (err) console.error('审计日志写入失败:', err.message);
    });
}

// 交易日历：周一至周五，法定节假日（data/holidays.json，无文件时仅按周末判断）
function isTradingDay(date) {
  const d = date || new Date();
  const day = d.getDay();
  if (day === 0 || day === 6) return false;
  try {
    const list = JSON.parse(fs.readFileSync(path.join(__dirname, 'data', 'holidays.json'), 'utf8'));
    const ds = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    return !(list.holidays || []).includes(ds);
  } catch (e) {
    return true;
  }
}

// 盘后订单确认任务：每日 20:00 确认前一日（含更早）SUBMITTED 订单（T+1 规则）
function schedulePostCloseConfirmation() {
  const run = () => {
    confirmPendingOrders({ db, saveTransaction, updateHolding, audit }).then(r => {
      console.log(\`[订单确认] 完成 \${r.confirmed} 笔\` + (r.errors.length ? \`，错误: \${r.errors.join('; ')}\` : ''));
    }).catch(e => console.error('[订单确认] 失败:', e.message));
  };
  const now = new Date();
  const target = new Date(now);
  target.setHours(20, 0, 0, 0);
  if (now > target) target.setDate(target.getDate() + 1);
  const delay = target.getTime() - now.getTime();
  console.log(\`[订单确认] 下次确认: \${target.toLocaleString('zh-CN')}\`);
  setTimeout(() => {
    run();
    setInterval(run, 24 * 60 * 60 * 1000);
  }, delay);
}

`;
  s = s.replace(anchor, fns + anchor);
}

// R4: 收盘分析生成订单（锚点：计算目标价和止损价）
{
  const anchor = "        // 计算目标价和止损价";
  if (!s.includes(anchor)) fail('R4 锚点未找到');
  const inject = `        // 收盘决策 → 生成真实订单（T 日下单，T+1 确认；不立即动持仓/现金）
        if (analysisType === 'close' && (action === 'buy' || action === 'add') && currentNav > 0) {
          try {
            const holding = portfolio.holdings[fundCode];
            const hasHolding = !!holding && holding.shares > 0;
            if (!hasHolding) {
              const ratio = action === 'buy' ? 0.2 : 0.1;
              const suggestAmount = Math.round(portfolio.current_capital * ratio);
              if (suggestAmount >= 100) {
                const order = await orderEngine.createOrder({ db, audit }, {
                  userId, fundCode, orderType: 'BUY', amount: suggestAmount, price: currentNav,
                  reason: \`AI自动建仓：\${sig.signal.label}（\${sig.signal.reason}）\`
                });
                console.log(\`  → 生成买入订单#\${order.id} \${fundCode} ¥\${suggestAmount}（T+1确认）\`);
              } else {
                console.log(\`  → \${fundCode} 可用现金不足（¥\${portfolio.current_capital}），跳过下单\`);
              }
            }
          } catch (orderErr) {
            console.error(\`生成订单失败 \${fundCode}:\`, orderErr.message);
          }
        }

        // 计算目标价和止损价`;
  s = s.replace(anchor, inject);
}

// R5: scheduleAnalysis 注册盘后确认任务
{
  const old = "  // 3. 收盘分析 - 每日15:00\n  scheduleCloseAnalysis();\n}";
  if (!s.includes(old)) fail('R5 锚点未找到');
  s = s.replace(old, "  // 3. 收盘分析 - 每日15:00\n  scheduleCloseAnalysis();\n  \n  // 4. 盘后订单确认 - 每日20:00（T+1确认）\n  schedulePostCloseConfirmation();\n}");
}

// R6: 启动时恢复确认 + 新 API
{
  const old = "  // 启动定时任务\n  scheduleAnalysis();";
  if (!s.includes(old)) fail('R6a 锚点未找到');
  s = s.replace(old, `  // 启动定时任务
  scheduleAnalysis();

  // 启动时确认跨交易日未确认订单（恢复场景）
  setTimeout(() => {
    confirmPendingOrders({ db, saveTransaction, updateHolding, audit }).then(r => {
      console.log(\`[订单确认] 启动恢复确认 \${r.confirmed} 笔\` + (r.errors.length ? \`，错误 \${r.errors.length}\` : ''));
    }).catch(e => console.error('[订单确认] 启动恢复失败:', e.message));
  }, 3000);`);
}

// R6b: 新 API（锚点：GET /api/users 前）
{
  const anchor = "app.get('/api/users', (req, res) => {";
  if (!s.includes(anchor)) fail('R6b 锚点未找到');
  const apis = `// ============ P0-1 新增 API：订单/审计/调度状态 ============
app.get('/api/orders', (req, res) => {
  const userId = req.query.user_id || currentUser;
  const limit = Math.min(parseInt(req.query.limit) || 50, 200);
  db.all('SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT ?', [userId, limit], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ orders: rows });
  });
});

app.get('/api/audit', (req, res) => {
  const limit = Math.min(parseInt(req.query.limit) || 100, 500);
  db.all('SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?', [limit], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ logs: rows });
  });
});

app.get('/api/scheduler/status', (req, res) => {
  res.json({
    trading_day: isTradingDay(new Date()),
    tasks: ['realtime(30min)', 'pre_close(14:30)', 'close(15:00)', 'post_close_confirm(20:00)', 'daily_backup(23:30)']
  });
});

`;
  s = s.replace(anchor, apis + anchor);
}

// R7: order-engine 确认条件改为 order_date < today（严格 T+1：今天下的单明天确认）
{
  const p2 = 'C:/Users/jiancent/WorkBuddy/fund/fund-simulator/engine/order-engine.js';
  let s2 = fs.readFileSync(p2, 'utf8');
  const oldQ = "AND order_date <= ?";
  if (!s2.includes(oldQ)) fail('R7 锚点未找到');
  s2 = s2.replace(oldQ, "AND order_date < ?");
  fs.writeFileSync(p2, s2, 'utf8');
  console.log('order-engine.js: 确认条件改为 order_date < 今日（严格 T+1）');
}

if (s === before) fail('没有任何替换发生');
fs.writeFileSync(p, s, 'utf8');
console.log('server.js 改造完成，新长度:', s.length);
