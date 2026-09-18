# -*- coding: utf-8 -*-
"""修正 fund-daily-pnl：份额按天延续（无交易日继承前值）；只返回持仓期间（首次交易日起）"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """    // 每日收盘后份额重建（交易当日生效）
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
    res.json({ user_id: userId, fund_code: fundCode, data: rows });"""
new = """    // 每日收盘后份额重建：有交易日的份额为交易后值，无交易日继承前一日
    const dayShares = {};
    let shares = 0;
    let firstDay = null;
    for (const tx of txs) {
      const day = String(tx.transaction_date).slice(0, 10);
      if (tx.transaction_type === 'BUY') shares += tx.shares; else shares -= tx.shares;
      dayShares[day] = shares;
      if (firstDay === null || day < firstDay) firstDay = day;
    }
    // T+1：买入当日无收益
    const buyDays = new Set(txs.filter(t => t.transaction_type === 'BUY').map(t => String(t.transaction_date).slice(0, 10)));
    const rows = [];
    let lastShares = 0;
    for (let i = 0; i < navs.length; i++) {
      const n = navs[i];
      if (n.nav_date < firstDay) continue; // 只返回持仓期间（首次交易日起）
      if (dayShares[n.nav_date] !== undefined) lastShares = dayShares[n.nav_date];
      const sh = lastShares;
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
    res.json({ user_id: userId, fund_code: fundCode, data: rows });"""
assert s.count(old) == 1, 'block not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('server.js patched')
