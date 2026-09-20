# -*- coding: utf-8 -*-
"""后端新增 /api/ai/daily-pnl（账户级每日收益明细，按日各基金贡献+账户快照对照）与 /api/ai/fund-fees（单基金费率）"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

anchor = """app.get('/api/users', async (req, res) => {"""
api = """// ===== 账户级每日收益明细（跨基金按日贡献；账户快照对照含费口径）=====
app.get('/api/ai/daily-pnl', async (req, res) => {
  try {
    const userId = req.query.user_id || currentUser;
    const all = (sql, params = []) => new Promise((resolve, reject) => db.all(sql, params, (e, r) => e ? reject(e) : resolve(r || [])));
    const codes = await all('SELECT DISTINCT fund_code FROM transactions WHERE user_id = ?', [userId]);
    const dayMap = {};
    const nameMap = {};
    for (const row of codes) {
      const fundCode = row.fund_code;
      const fund = await new Promise((resolve) => db.get('SELECT fund_name FROM funds WHERE fund_code = ?', [fundCode], (e, r) => resolve(r || null)));
      nameMap[fundCode] = fund ? fund.fund_name : fundCode;
      const txs = await all('SELECT transaction_type, shares, transaction_date FROM transactions WHERE user_id = ? AND fund_code = ? ORDER BY transaction_date ASC', [userId, fundCode]);
      const navs = await all('SELECT nav_date, unit_nav FROM fund_nav WHERE fund_code = ? ORDER BY nav_date ASC', [fundCode]);
      const dayShares = {};
      let shares = 0;
      let firstDay = null;
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
      date,
      pnl: Math.round(dayMap[date].total * 100) / 100,
      account_pnl: snapMap[date] != null ? snapMap[date] : null,
      funds: dayMap[date].funds
    }));
    res.json({ list: rows, fund_names: nameMap });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ===== 单基金费率（申购/赎回阶梯/管理/托管，真实 fund_fees）=====
app.get('/api/ai/fund-fees', async (req, res) => {
  try {
    const fundCode = req.query.fund_code;
    if (!fundCode) return res.status(400).json({ error: 'fund_code required' });
    const fee = await new Promise((resolve) => db.get('SELECT * FROM fund_fees WHERE fund_code = ?', [fundCode], (e, r) => resolve(r || null)));
    if (!fee) return res.json({ fund_code: fundCode, found: false });
    let schedule = [];
    try { schedule = JSON.parse(fee.sell_schedule || '[]'); } catch (e) { schedule = []; }
    const pct = v => v == null ? null : (v * 100);
    res.json({
      fund_code: fundCode, found: true,
      buy_fee_pct: pct(fee.buy_fee_pct),
      manage_fee_pct: pct(fee.manage_fee_pct),
      custody_fee_pct: pct(fee.custody_fee_pct),
      service_fee_pct: pct(fee.service_fee_pct),
      sell_schedule: schedule.map(x => ({ days: x.days, rate_pct: Math.round(x.rate * 10000) / 100 })),
      updated_at: fee.updated_at
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 用户管理API
app.get('/api/users', async (req, res) => {"""
assert s.count(anchor) == 1, 'anchor not found'
s = s.replace(anchor, api)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('server.js patched')
