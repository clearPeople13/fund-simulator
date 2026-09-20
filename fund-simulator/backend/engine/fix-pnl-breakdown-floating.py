# -*- coding: utf-8 -*-
"""修正收益构成浮动盈亏口径：用 holdings.pnl（已处理 T+1 待确认→0），避免待确认基金 market_value 计入浮动"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """  const realized = p.realized_pnl || 0
  const hs = holdings.value
  const floating = hs.reduce((sum, h) => sum + ((h.market_value || 0) - (h.total_cost || 0)), 0)"""
new = """  const realized = p.realized_pnl || 0
  const hs = holdings.value
  // 浮动盈亏用 loadHoldingsDetail 的 pnl 字段（已处理 T+1 待确认→0），避免待确认基金市值差误入浮动
  const floating = hs.reduce((sum, h) => sum + (h.pnl || 0), 0)"""
assert s.count(old) == 1, 'block not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Home.vue patched')
