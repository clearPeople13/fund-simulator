# -*- coding: utf-8 -*-
"""后端新增 /api/ai/fund-daily-pnl：单基金每日收益明细（日期/当日涨幅/当日持有份额/当日盈亏金额），T+1 买入当日无收益"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

anchor = """// 获取AI交易记录
app.get('/api/ai/transactions', async (req, res) => {"""
api = """// 单基金每日收益明细：日期 / 当日涨幅 / 当日持有份额 / 当日盈亏金额（T+1：买入当日无收益）
app.get('/api/ai/fund-daily-pnl', async (req, res) => {
  try {
    const userId = req.query.user_id || currentUser;
    const fundCode = req.query.fund_code;
    if (!fundCode) return res.status(400).json({ error: 'fund_code required' });
    const txs = await new Promise((resolve, reject) => {
      db.all("SELECT transaction_type, shares, transaction_date FROM transactions WHERE user_id = ? AND fund_code = ? ORDER BY transaction_date ASC", [userId, fundCode], (err, r) => err ? reject(err) : resolve(r || []));
    });
    const navs = await new Promise((resolve, reject) => {
      db.all("SELECT nav_date, unit_nav, daily_return FROM fund_nav WHERE fund_code = ? ORDER BY nav_date ASC", [fundCode], (err, r) => err ? reject(err) : resolve(r || []));
    });
    // 每日收盘后份额重建（交易当日生效）
    const dayShares = {};
    let shares = 0;
    for (const tx of txs) {
      const day = String(tx.transaction_date).slice(0, 10);
      if (tx.transaction_type === 'BUY') shares += tx.shares; else shares -= tx.shares;
      dayShares[day] = shares;
    }
    // T+1：买入当日无收益
    const buyDays = new Set(txs.filter(t => t.transaction_type === 'BUY').map(t => String(t.transaction_date).slice(0, 10)));
    const rows = [];
    for (let i = 0; i < navs.length; i++) {
      const n = navs[i];
      const sh = dayShares[n.nav_date] || 0;
      let pnl = 0;
      if (i > 0 && sh > 0) {
        pnl = sh * (n.unit_nav - navs[i - 1].unit_nav);
      }
      if (buyDays.has(n.nav_date)) pnl = 0; // 当日买入 T+1 无收益
      rows.push({
        date: n.nav_date,
        nav: n.unit_nav,
        daily_return: n.daily_return,
        shares: Math.round(sh * 1000) / 1000,
        pnl: Math.round(pnl * 100) / 100
      });
    }
    res.json({ user_id: userId, fund_code: fundCode, data: rows });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 获取AI交易记录
app.get('/api/ai/transactions', async (req, res) => {"""
assert s.count(anchor) == 1, 'anchor not found'
s = s.replace(anchor, api)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('server.js patched')
