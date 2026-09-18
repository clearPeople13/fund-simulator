# -*- coding: utf-8 -*-
"""后端：/api/ai/portfolio 每只持仓附加 realized_pnl（该基金累计已实现，精确对账）；前端卖出行收益用系统账本"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old1 = """      const latestNav = navRow ? navRow.unit_nav : null;
      // T+1 待确认持仓按成本计市值（当日买入当日无收益，不计浮盈）
      const marketValue = pending ? h.total_cost : (latestNav ? h.shares * latestNav : h.total_cost);
      holdings[code] = {
        ...h, fund_name: fund ? fund.fund_name : code, fund_type: fund ? fund.fund_type : '', pending_confirm: pending,
        latest_nav: latestNav, nav_date: navRow ? navRow.nav_date : null, daily_return: navRow ? navRow.daily_return : null,
        market_value: marketValue
      };"""
new1 = """      const latestNav = navRow ? navRow.unit_nav : null;
      // T+1 待确认持仓按成本计市值（当日买入当日无收益，不计浮盈）
      const marketValue = pending ? h.total_cost : (latestNav ? h.shares * latestNav : h.total_cost);
      // 该基金累计已实现盈亏（realized_pnl 账本，精确对账）
      const realizedRow = await new Promise((resolve) => {
        db.get('SELECT SUM(amount) AS t FROM realized_pnl WHERE user_id = ? AND fund_code = ?', [userId, code], (err, row) => resolve(err ? null : row));
      });
      holdings[code] = {
        ...h, fund_name: fund ? fund.fund_name : code, fund_type: fund ? fund.fund_type : '', pending_confirm: pending,
        latest_nav: latestNav, nav_date: navRow ? navRow.nav_date : null, daily_return: navRow ? navRow.daily_return : null,
        market_value: marketValue,
        realized_pnl: realizedRow && realizedRow.t ? Math.round(realizedRow.t * 100) / 100 : 0
      };"""
assert s.count(old1) == 1, 'backend block not found'
s = s.replace(old1, new1)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('server.js patched')

# 前端：卖出行收益优先用系统账本 realized_pnl
p2 = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p2, 'r', encoding='utf-8') as f:
    s2 = f.read()
old2 = """    } else {
      // 卖出：已实现盈亏 = 净到账 - 卖出份额×平均成本（含费摊薄）
      const cost = avgCost * tx.shares
      pnl = cost > 0 ? (tx.amount - (tx.fees || 0)) - cost : null
      pnlRate = pnl != null && cost > 0 ? (pnl / cost) * 100 : null
      pnlTag = '实'
    }"""
new2 = """    } else {
      // 卖出：已实现盈亏优先取系统账本 realized_pnl（精确对账）；无账本时按平均成本估算
      const realized = hold && hold.realized_pnl != null ? hold.realized_pnl : null
      const cost = avgCost * tx.shares
      pnl = realized != null ? realized : (cost > 0 ? (tx.amount - (tx.fees || 0)) - cost : null)
      pnlRate = pnl != null && cost > 0 ? (pnl / cost) * 100 : null
      pnlTag = '实'
    }"""
assert s2.count(old2) == 1, 'frontend block not found'
s2 = s2.replace(old2, new2)
with io.open(p2, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s2)
print('Home.vue patched')
