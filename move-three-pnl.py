import io

# 1) readonly.js 加四个路由
p1 = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\routes\readonly.js"
with io.open(p1, 'r', encoding='utf-8') as f:
    s1 = f.read()
old = "  r.get('/analysis/logs', async (req, res) => {"
new = """  r.get('/ai/fund-daily-pnl', async (req, res) => {
    try {
      const userId = req.query.user_id || getCurrentUser();
      const fundCode = req.query.fund_code;
      if (!fundCode) return res.status(400).json({ error: 'fund_code required' });
      const txs = await new Promise((resolve, reject) => {
        db.all("SELECT transaction_type, shares, transaction_date FROM transactions WHERE user_id = ? AND fund_code = ? ORDER BY transaction_date ASC", [userId, fundCode], (e, r) => e ? reject(e) : resolve(r || []));
      });
      const navs = await new Promise((resolve, reject) => {
        db.all("SELECT nav_date, unit_nav, daily_return FROM fund_nav WHERE fund_code = ? ORDER BY nav_date ASC", [fundCode], (e, r) => e ? reject(e) : resolve(r || []));
      });
      const dayShares = {}; let shares = 0; let firstDay = null;
      for (const tx of txs) {
        const day = String(tx.transaction_date).slice(0, 10);
        if (tx.transaction_type === 'BUY') shares += tx.shares; else shares -= tx.shares;
        dayShares[day] = shares;
        if (firstDay === null || day < firstDay) firstDay = day;
      }
      const buyDays = new Set(txs.filter(t => t.transaction_type === 'BUY').map(t => String(t.transaction_date).slice(0, 10)));
      const rows = []; let lastShares = 0;
      for (let i = 0; i < navs.length; i++) {
        const n = navs[i];
        if (n.nav_date < firstDay) continue;
        if (dayShares[n.nav_date] !== undefined) lastShares = dayShares[n.nav_date];
        const sh = lastShares; let pnl = 0;
        if (i > 0 && sh > 0) pnl = sh * (n.unit_nav - navs[i - 1].unit_nav);
        if (buyDays.has(n.nav_date)) pnl = 0;
        rows.push({ date: n.nav_date, nav: n.unit_nav, daily_return: n.daily_return, shares: Math.round(sh * 1000) / 1000, pnl: Math.round(pnl * 100) / 100 });
      }
      res.json({ user_id: userId, fund_code: fundCode, data: rows });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.get('/ai/daily-pnl', async (req, res) => {
    try {
      const userId = req.query.user_id || getCurrentUser();
      const all = (sql, params = []) => new Promise((resolve, reject) => db.all(sql, params, (e, r) => e ? reject(e) : resolve(r || [])));
      const codes = await all('SELECT DISTINCT fund_code FROM transactions WHERE user_id = ?', [userId]);
      const dayMap = {}; const nameMap = {};
      for (const row of codes) {
        const fundCode = row.fund_code;
        const fund = await new Promise((resolve) => db.get('SELECT fund_name FROM funds WHERE fund_code = ?', [fundCode], (e, r) => resolve(r || null)));
        nameMap[fundCode] = fund ? fund.fund_name : fundCode;
        const txs = await all('SELECT transaction_type, shares, transaction_date FROM transactions WHERE user_id = ? AND fund_code = ? ORDER BY transaction_date ASC', [userId, fundCode]);
        const navs = await all('SELECT nav_date, unit_nav FROM fund_nav WHERE fund_code = ? ORDER BY nav_date ASC', [fundCode]);
        const dayShares = {}; let shares = 0; let firstDay = null;
        for (const tx of txs) {
          const day = String(tx.transaction_date).slice(0, 10);
          if (tx.transaction_type === 'BUY') shares += tx.shares; else shares -= tx.shares;
          dayShares[day] = shares;
          if (firstDay === null || day < firstDay) firstDay = day;
        }
        const buyDays = new Set(txs.filter(t => t.transaction_type === 'BUY').map(t => String(t.transaction_date).slice(0, 10)));
        let lastShares = 0;
        for (let i = 0; i < navs.length; i++) {
          const n = navs[i];
          if (n.nav_date < firstDay) continue;
          if (dayShares[n.nav_date] !== undefined) lastShares = dayShares[n.nav_date];
          let pnl = 0;
          if (i > 0 && lastShares > 0) pnl = lastShares * (n.unit_nav - navs[i - 1].unit_nav);
          if (buyDays.has(n.nav_date)) pnl = 0;
          pnl = Math.round(pnl * 100) / 100;
          if (pnl === 0 && lastShares === 0) continue;
          dayMap[n.nav_date] = dayMap[n.nav_date] || { total: 0, funds: {} };
          dayMap[n.nav_date].funds[fundCode] = pnl;
          dayMap[n.nav_date].total += pnl;
        }
      }
      const snaps = await all('SELECT date, daily_pnl FROM portfolio_daily WHERE user_id = ? ORDER BY date ASC', [userId]);
      const snapMap = {};
      (snaps || []).forEach(x => { snapMap[x.date] = x.daily_pnl; });
      const rows = Object.keys(dayMap).sort().map(date => ({
        date, pnl: Math.round(dayMap[date].total * 100) / 100,
        account_pnl: snapMap[date] != null ? snapMap[date] : null,
        funds: dayMap[date].funds
      }));
      res.json({ list: rows, fund_names: nameMap });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.get('/ai/performance-vs-benchmark', async (req, res) => {
    const qall = (sql, params = []) => new Promise((resolve, reject) => db.all(sql, params, (e, r) => e ? reject(e) : resolve(r || [])));
    try {
      const userId = req.query.user_id || getCurrentUser();
      const snaps = await qall('SELECT date, total_assets FROM portfolio_daily WHERE user_id = ? ORDER BY date ASC', [userId]);
      const cfg = await new Promise((resolve) => db.get('SELECT initial_capital FROM user_configs WHERE user_id = ?', [userId], (e, r) => resolve(r || null)));
      const initial = (cfg && cfg.initial_capital) || 100000;
      const bench = await qall('SELECT date, value FROM benchmark_daily ORDER BY date ASC');
      const accMap = {}, benchMap = {};
      snaps.forEach(s => { accMap[s.date] = Math.round((s.total_assets / initial - 1) * 10000) / 100; });
      if (bench.length) {
        const base = bench[0].value || 1;
        bench.forEach(b => { benchMap[b.date] = Math.round((b.value / base - 1) * 10000) / 100; });
      }
      const dates = [...new Set([...Object.keys(accMap), ...Object.keys(benchMap)])].sort();
      res.json({ initial_capital: initial, series: dates.map(d => ({
        date: d, account_pct: accMap[d] != null ? accMap[d] : null, bench_pct: benchMap[d] != null ? benchMap[d] : null
      })) });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.get('/analysis/logs', async (req, res) => {"""
assert s1.count(old) == 1
s1 = s1.replace(old, new)
with io.open(p1, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s1)

# 2) server.js 删这三个路由块
p2 = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p2, 'r', encoding='utf-8') as f:
    s2 = f.read()

# fund-daily-pnl
start1 = s2.find("app.get('/api/ai/fund-daily-pnl', async (req, res) => {")
end1 = s2.find("// 获取AI交易记录", start1)
assert start1 != -1 and end1 != -1
s2 = s2[:start1] + "// /api/ai/fund-daily-pnl 已抽到 routes/readonly.js\n" + s2[end1:]

# daily-pnl
start2 = s2.find("app.get('/api/ai/daily-pnl', async (req, res) => {")
end2 = s2.find("// 账户累计收益率 vs 沪深300", start2)
assert start2 != -1 and end2 != -1
s2 = s2[:start2] + "// /api/ai/daily-pnl 已抽到 routes/readonly.js\n" + s2[end2:]

# performance-vs-benchmark
start3 = s2.find("app.get('/api/ai/performance-vs-benchmark', async (req, res) => {")
end3 = s2.find("// ===== 单基金费率", start3)
assert start3 != -1 and end3 != -1
s2 = s2[:start3] + "// /api/ai/performance-vs-benchmark 已抽到 routes/readonly.js\n" + s2[end3:]

with io.open(p2, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s2)
print('three routes moved')
