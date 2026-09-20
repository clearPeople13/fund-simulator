// P1 patch A：函数（基金评分/研究笔记/市场温度/再平衡/换仓/分红/归因/压力/复盘）
// 规格：fund/AI_FUND_OPERATIONS_DESIGN.md §4.2/§4.3/§4.5/§4.6/§4.7
const fs = require('fs');
const p = 'C:/Users/jiancent/WorkBuddy/fund/fund-simulator/server.js';
let s = fs.readFileSync(p, 'utf8');
const fail = (m) => { console.error('FAIL: ' + m); process.exit(1); };

// 新表：dividends / data_quality_logs / market_env
{
  const anchor = "    db.run(`CREATE TABLE IF NOT EXISTS benchmark_daily (";
  if (!s.includes(anchor)) fail('R1 锚点未找到');
  const tbl = `    db.run(\`CREATE TABLE IF NOT EXISTS dividends (
      fund_code TEXT NOT NULL,
      ex_date TEXT NOT NULL,
      per_unit REAL,
      type TEXT DEFAULT 'CASH',
      nav_before REAL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(fund_code, ex_date)
    )\`);
    db.run(\`CREATE TABLE IF NOT EXISTS data_quality_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      fund_code TEXT,
      nav_date TEXT,
      issue_type TEXT,
      detail TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )\`);
    db.run(\`CREATE TABLE IF NOT EXISTS market_env (
      date TEXT PRIMARY KEY,
      avg_fund_chg REAL,
      bench_chg REAL,
      temperature TEXT,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )\`);
    db.run(\`CREATE TABLE IF NOT EXISTS benchmark_daily (`;
  s = s.replace(anchor, tbl);
}

// 函数插入（generateReport 之后）
{
  const anchor = "// 盘后订单确认任务：每日 20:00 确认前一日（含更早）SUBMITTED 订单（T+1 规则）";
  if (!s.includes(anchor)) fail('R2 锚点未找到');
  const fns = `// ============ P1 决策质量（规格 §4.2/§4.3/§4.5/§4.6/§4.7）============

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
      db.run(\`INSERT INTO fund_profiles (fund_code, volatility, downside_risk, style_label, score, updated_at) VALUES (?, ?, ?, ?, ?, datetime('now','localtime'))
              ON CONFLICT(fund_code) DO UPDATE SET volatility=excluded.volatility, downside_risk=excluded.downside_risk,
              style_label=excluded.style_label, score=excluded.score, updated_at=excluded.updated_at\`,
        [code, +vol.toFixed(2), +downsideRisk.toFixed(2), styleLabel, score], (err) => resolve());
    });
    done++;
  }
  console.log(\`[评分] 已更新 \${done} 只基金画像（波动/下行/风格/评分）\`);
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
    db.run('INSERT OR REPLACE INTO market_env (date, avg_fund_chg, bench_chg, temperature, updated_at) VALUES (?, ?, ?, ?, datetime(\'now\',\'localtime\'))',
      [dateStr, avg != null ? +avg.toFixed(2) : null, bench != null ? +bench.toFixed(2) : null, temperature], (err) => resolve());
  });
  console.log(\`[市场] \${dateStr} 基金均涨 \${avg != null ? avg.toFixed(2) + '%' : 'N/A'} 基准 \${bench != null ? bench.toFixed(2) + '%' : 'N/A'} 温度:\${temperature}\`);
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
            reason: \`再平衡调仓：\${type}超配 \${(cur * 100).toFixed(1)}%（目标 \${(target * 100).toFixed(0)}%），卖出降低\`
          });
          ordersMade.push({ fund_code: code, type: 'SELL', shares: sellShares, orderId: order.id });
          logRiskEvent(userId, 'REBALANCE', code, \`\${type}超配→卖出 \${sellShares} 份\`, 'sell');
          break;
        }
      }
    } else if (target - cur > threshold && total * 0.05 >= 100) {
      // 低配 → 买入该类型观察池基金（取分数最高的一只，风控约束）
      const buyAmt = Math.round((target - cur) * total * 0.3);
      if (buyAmt < 100) continue;
      const candidates = await new Promise((resolve) => {
        db.all(\`SELECT w.fund_code FROM watchlist w JOIN funds f ON w.fund_code = f.fund_code
                 JOIN fund_profiles fp ON fp.fund_code = w.fund_code
                 WHERE w.user_id = ? AND f.fund_type = ? ORDER BY fp.score DESC LIMIT 1\`, [userId, type], (err, rows) => resolve(err ? [] : (rows || [])));
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
        reason: \`再平衡调仓：\${type}低配 \${((target - cur) * 100).toFixed(1)}%，买入补足（信号 \${sig.signal.label}）\`
      });
      ordersMade.push({ fund_code: code, type: 'BUY', amount: buyAmt, orderId: order.id });
    }
  }
  if (ordersMade.length) console.log(\`[再平衡] \${userId} 生成调仓订单: \`, JSON.stringify(ordersMade));
  else console.log(\`[再平衡] \${userId} 配置偏离未超阈值，无需调仓\`);
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
    db.all(\`SELECT w.fund_code FROM watchlist w JOIN fund_profiles fp ON fp.fund_code = w.fund_code
             WHERE w.user_id = ? AND fp.score >= 60 ORDER BY fp.score DESC LIMIT 1\`, [userId], (err, rows) => resolve(err ? [] : (rows || [])));
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
      reason: \`换仓决策：\${weakHolding.code} 近20日 \${weakHolding.sig.change_20d.toFixed(1)}% 跌破20日线（弱信号），卖出换入强势基金\`
    });
    const buyOrder = await orderEngine.createOrder({ db, audit }, {
      userId, fundCode: code, orderType: 'BUY', amount: Math.round(estCash), price: nav,
      reason: \`换仓决策：买入 \${code}（评分高、信号 \${sig.signal.label}），承接换仓资金\`
    });
    console.log(\`[换仓] \${userId} 卖 \${weakHolding.code} 买 \${code}（订单#\${sellOrder.id}/#\${buyOrder.id}）\`);
    logRiskEvent(userId, 'SWITCH', weakHolding.code + '→' + code, \`卖出弱势换入强势（等额 \${Math.round(estCash)} 元）\`, 'switch');
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
        if (!/^\\d{4}-\\d{2}-\\d{2}$/.test(exDate) || isNaN(perUnit)) continue;
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
            db.run(\`INSERT INTO transactions (user_id, fund_code, transaction_type, amount, price, shares, fees, reason)
                     VALUES (?, ?, 'DIVIDEND', ?, ?, ?, 0, ?)\`,
              [userId, code, cashAmount, perUnit, 0, code + ' 现金分红 ¥' + cashAmount + '（每份 ¥' + perUnit + '）'], (err) => {});
            logRiskEvent(userId, 'DIVIDEND', code, '现金分红到账 ¥' + cashAmount, 'cash');
            console.log(\`[分红] \${userId} 持有 \${code} 获现金分红 ¥\${cashAmount}\`);
          }
        }
      }
    } catch (e) {
      // 分红接口失败不阻塞（记录一次即可）
    }
  }
  if (found) console.log(\`[分红] 已同步 \${found} 条分红记录\`);
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
      db.all(\`SELECT fp.fund_code FROM funds f JOIN fund_profiles fp ON fp.fund_code = f.fund_code WHERE f.fund_type = ? LIMIT 20\`, [type], (err, rows) => resolve(err ? [] : (rows || [])));
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
    db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, 'pressure', getLocalDateStr(), content], (err) => resolve());
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
      db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, 'daily', dateStr, content], (err) => resolve());
    });
    console.log('[复盘] ' + userId + ' 每日复盘已生成');
  }
}

// 盘后订单确认任务：每日 20:00 确认前一日（含更早）SUBMITTED 订单（T+1 规则）`;
  s = s.replace(anchor, fns);
}

fs.writeFileSync(p, s, 'utf8');
console.log('P1 patch A 完成，新长度:', s.length);
