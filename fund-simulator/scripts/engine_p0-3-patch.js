// P0-3 改造脚本：基准指数接入 + performance_daily 绩效 + 周报/月报
// 规格：fund/AI_FUND_OPERATIONS_DESIGN.md §4.5 §5.2
const fs = require('fs');
const p = 'C:/Users/jiancent/WorkBuddy/fund/fund-simulator/server.js';
let s = fs.readFileSync(p, 'utf8');
const fail = (m) => { console.error('FAIL: ' + m); process.exit(1); };

// R1: benchmark_daily 表
{
  const anchor = "    db.run(`CREATE TABLE IF NOT EXISTS research_notes (";
  if (!s.includes(anchor)) fail('R1 锚点未找到');
  const tbl = `    db.run(\`CREATE TABLE IF NOT EXISTS benchmark_daily (
      date TEXT PRIMARY KEY,
      value REAL,
      change_pct REAL,
      source TEXT DEFAULT 'eastmoney'
    )\`);
    db.run(\`CREATE TABLE IF NOT EXISTS research_notes (`;
  s = s.replace(anchor, tbl);
}

// R2: 函数（fetchBenchmark / computePerformance / generateReport）
{
  const anchor = "// 盘后订单确认任务：每日 20:00 确认前一日（含更早）SUBMITTED 订单（T+1 规则）";
  if (!s.includes(anchor)) fail('R2 锚点未找到');
  const fns = `// ============ P0-3 绩效与报告（规格 §4.5/§5.2）============

// 抓取沪深300指数收盘点位（东方财富 K 线接口，UTF-8 JSON，真实数据）
async function fetchBenchmark() {
  try {
    const url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get';
    const resp = await axios.get(url, {
      params: {
        secid: '1.000300', fields1: 'f1,f2,f3,f4,f5,f6',
        fields2: 'f51,f53', klt: '101', fqt: '0',
        beg: '20260101', end: '20500101', lmt: '15'
      },
      timeout: 12000
    });
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
    console.log(\`[基准] 沪深300 已更新 \${saved} 个交易日，最新: \${klines[klines.length - 1]}\`);
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
  const totalReturn = initial > 0 ? (pf.total_assets / initial - 1) * 100 : 0;

  // 基准收益：从首个快照日到 dateStr
  const benchRow = await new Promise((resolve) => {
    db.get('SELECT value FROM benchmark_daily WHERE date <= ? ORDER BY date DESC LIMIT 1', [dateStr], (err, row) => resolve(err ? null : row));
  });
  const benchFirst = await new Promise((resolve) => {
    db.get('SELECT value FROM benchmark_daily ORDER BY date ASC LIMIT 1', [], (err, row) => resolve(err ? null : row));
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
    db.run(\`INSERT INTO performance_daily (user_id, date, total_return, benchmark_return, excess_return, volatility, sharpe, max_drawdown) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET total_return=excluded.total_return, benchmark_return=excluded.benchmark_return,
            excess_return=excluded.excess_return, volatility=excluded.volatility, sharpe=excluded.sharpe, max_drawdown=excluded.max_drawdown\`,
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
  lines.push(\`# \${cfg.name}（\${cfg.style}）\${reportType === 'weekly' ? '周报' : '月报'} \${rangeDesc}\`);
  lines.push('');
  lines.push(\`报告周期：\${period}\`);
  lines.push(\`当前总资产：¥\${pf.total_assets.toFixed(2)}（初始 ¥\${pf.initial_capital}）\`);
  lines.push(\`累计收益：\${(perf ? perf.total_return : 0).toFixed(2)}%\`);
  lines.push(\`基准（沪深300）同期：\${(perf ? perf.benchmark_return : 0).toFixed(2)}%\`);
  lines.push(\`超额收益：\${(perf ? perf.excess_return : 0).toFixed(2)}%\`);
  if (perf) {
    lines.push(\`年化波动率：\${perf.volatility.toFixed(2)}%　夏普比率：\${perf.sharpe.toFixed(2)}\`);
    lines.push(\`最大回撤：\${(perf.max_drawdown || 0).toFixed(2)}%\`);
  }
  lines.push('');
  lines.push('## 持仓明细');
  for (const [code, h] of Object.entries(pf.holdings)) {
    const nav = await new Promise((resolve) => {
      db.get('SELECT unit_nav FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1', [code], (err, row) => resolve(err ? null : row));
    });
    const mv = nav && nav.unit_nav ? h.shares * nav.unit_nav : h.total_cost;
    lines.push(\`- \${code}：\${h.shares}份　成本¥\${h.total_cost.toFixed(2)}　市值约¥\${mv.toFixed(2)}　盈亏 \${h.cost > 0 ? ((((nav ? nav.unit_nav : h.cost) / h.cost) - 1) * 100).toFixed(2) + '%' : '-'}\`);
  }
  lines.push('');
  lines.push('## 期间交易');
  if (trades.length === 0 && orders.length === 0) lines.push('- 无成交');
  for (const o of orders) lines.push(\`- [订单#\${o.id}] \${o.fund_code} \${o.order_type} \${o.order_type === 'BUY' ? '¥' + o.amount : o.shares + '份'} \${o.order_date}（\${o.reason || ''}）\`);
  lines.push('');
  lines.push('## 风控事件');
  if (events.length === 0) lines.push('- 无');
  for (const ev of events) lines.push(\`- [\${ev.event_type}] \${ev.fund_code || ''} \${ev.detail}（\${ev.created_at}）\`);
  lines.push('');
  lines.push('## 下周计划');
  lines.push(\`- 按 \${cfg.rebalance_frequency || 'monthly'} 再平衡节奏评估调仓；\`);
  lines.push(\`- 观察池 \${cfg.watchlist_style || ''} 标的持续跟踪，\${cfg.entry_signal_threshold || 'strong'} 信号才建仓；\`);
  lines.push(\`- 止损线 -\${((cfg.stop_loss || 0.05) * 100).toFixed(0)}%，止盈线 +\${((cfg.take_profit || 0.2) * 100).toFixed(0)}%，回撤熔断 -\${((cfg.max_drawdown || 0.1) * 100).toFixed(0)}%。\`);

  const content = lines.join('\\n');
  await new Promise((resolve) => {
    db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, reportType, period, content], (err) => resolve());
  });
  return { userId, reportType, period, content };
}

// 盘后订单确认任务：每日 20:00 确认前一日（含更早）SUBMITTED 订单（T+1 规则）`;
  s = s.replace(anchor, fns);
}

// R3: close 末尾接入（基准更新 + 绩效 + 周/月报）
{
  const anchor = "    console.log(`\\n=== ${typeNames[analysisType]}完成 ===\\n`);";
  if (!s.includes(anchor)) fail('R3 锚点未找到');
  const inject = `    // ===== P0-3：基准指数更新 + 绩效计算 + 周报/月报 =====
    if (analysisType === 'close') {
      await fetchBenchmark();
      const todayStr = getLocalDateStr();
      const now = new Date();
      const dayOfWeek = now.getDay();
      const isLastTradingDayOfMonth = dayOfWeek === 5 && (now.getDate() + 7 > new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate());
      for (const userId of Object.keys(userConfigs)) {
        try {
          const perf = await computePerformance(userId, todayStr);
          console.log(\`[绩效] \${userId} 总收益\${perf.totalReturn.toFixed(2)}% 基准\${perf.benchReturn.toFixed(2)}% 超额\${perf.excessReturn.toFixed(2)}% 夏普\${perf.sharpe.toFixed(2)}\`);
          if (dayOfWeek === 5) {
            const rep = await generateReport(userId, 'weekly');
            console.log(\`[报告] \${userId} 周报已生成（\${rep.period}）\`);
          }
          if (isLastTradingDayOfMonth) {
            const rep = await generateReport(userId, 'monthly');
            console.log(\`[报告] \${userId} 月报已生成（\${rep.period}）\`);
          }
        } catch (perfErr) {
          console.error(\`[绩效] \${userId} 计算失败:\`, perfErr.message);
        }
      }
    }

    console.log(\`\\n=== \${typeNames[analysisType]}完成 ===\\n\`);`;
  s = s.replace(anchor, inject);
}

// R4: API（performance / reports）
{
  const anchor = "app.get('/api/risk/events', (req, res) => {";
  if (!s.includes(anchor)) fail('R4 锚点未找到');
  const apis = `app.get('/api/performance/:user_id', async (req, res) => {
  try {
    const rows = await new Promise((resolve, reject) => {
      db.all('SELECT * FROM performance_daily WHERE user_id = ? ORDER BY date', [req.params.user_id], (err, rows) => err ? reject(err) : resolve(rows || []));
    });
    res.json({ user_id: req.params.user_id, performance: rows });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.get('/api/benchmark', async (req, res) => {
  try {
    const limit = Math.min(parseInt(req.query.limit) || 60, 500);
    const rows = await new Promise((resolve, reject) => {
      db.all('SELECT * FROM benchmark_daily ORDER BY date DESC LIMIT ?', [limit], (err, rows) => err ? reject(err) : resolve(rows || []));
    });
    res.json({ benchmark: rows.reverse() });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.get('/api/reports', async (req, res) => {
  try {
    const userId = req.query.user_id || currentUser;
    const type = req.query.type || 'weekly';
    const rows = await new Promise((resolve, reject) => {
      db.all('SELECT * FROM reports WHERE user_id = ? AND report_type = ? ORDER BY id DESC LIMIT 10', [userId, type], (err, rows) => err ? reject(err) : resolve(rows || []));
    });
    res.json({ user_id: userId, reports: rows });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.get('/api/risk/events', (req, res) => {`;
  s = s.replace(anchor, apis);
}

fs.writeFileSync(p, s, 'utf8');
console.log('P0-3 patch 完成，新长度:', s.length);
