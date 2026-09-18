# -*- coding: utf-8 -*-
"""修正 todayPnl 聚合：存在非 T+1 持仓且今日盈亏未更新（净值未公布）→ 整体待更新，而不是 0"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """  // 回退：聚合持仓今日盈亏；若所有持仓今日盈亏均未更新（净值未公布），返回 null 表示待更新
  const sum = holdings.value.reduce((sum, h) => sum + (h.today_pnl ?? 0), 0)
  if (holdings.value.length > 0 && holdings.value.every(h => h.today_pnl === null || h.today_pnl === undefined)) return null
  return sum"""
new = """  // 回退：聚合持仓今日盈亏
  const hs = holdings.value
  if (hs.length === 0) return 0
  // 存在非 T+1 持仓的今日盈亏未更新（当日净值未公布）→ 整体待更新，不显示 0
  const anyUnsettled = hs.some(h => !h.pending_confirm && (h.today_pnl === null || h.today_pnl === undefined))
  if (anyUnsettled) return null
  return hs.reduce((sum, h) => sum + (h.today_pnl ?? 0), 0)"""
assert s.count(old) == 1, 'block not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Home.vue patched')
