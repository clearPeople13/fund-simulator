# -*- coding: utf-8 -*-
"""T+1 待确认持仓不计浮盈：市值按成本计入总资产（前后端统一）"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) saveDailySnapshot：当日买入持仓按成本计市值
old1 = """    if (!navRow || !navRow.unit_nav) continue;

    const mv = h.shares * navRow.unit_nav;
    marketValue += mv;

    // T+1 规则：当日买入的持仓当日无收益
    const lastBuy = await new Promise((resolve, reject) => {
      db.get("SELECT transaction_date FROM transactions WHERE user_id = ? AND fund_code = ? AND transaction_type = 'BUY' ORDER BY transaction_date DESC LIMIT 1",
        [userId, code], (err, row) => err ? reject(err) : resolve(row));
    });
    if (!lastBuy || !isSameLocalDay(lastBuy.transaction_date)) {
      todayPnl += mv * (navRow.daily_return || 0) / 100;
    }"""
new1 = """    if (!navRow || !navRow.unit_nav) continue;

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
    }"""
assert s.count(old1) == 1, 'snapshot block not found'
s = s.replace(old1, new1)

# 2) /api/ai/portfolio：pending_confirm 持仓市值按成本
old2 = """      const latestNav = navRow ? navRow.unit_nav : null;
      const marketValue = latestNav ? h.shares * latestNav : h.total_cost;"""
new2 = """      const latestNav = navRow ? navRow.unit_nav : null;
      // T+1 待确认持仓按成本计市值（当日买入当日无收益，不计浮盈）
      const marketValue = pending ? h.total_cost : (latestNav ? h.shares * latestNav : h.total_cost);"""
assert s.count(old2) == 1, 'portfolio block not found'
s = s.replace(old2, new2)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('server.js patched')
