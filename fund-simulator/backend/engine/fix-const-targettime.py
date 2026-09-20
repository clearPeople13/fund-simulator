# -*- coding: utf-8 -*-
"""修复：schedulePreCloseAnalysis / scheduleCloseAnalysis 中 targetTime 需重新赋值（nextTradingDay 顺延），const 改 let"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = "  const targetTime = new Date(now);"
assert s.count(old) == 2, 'expect 2 const targetTime, got %d' % s.count(old)
s = s.replace(old, "  let targetTime = new Date(now);")

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('fixed: const targetTime -> let targetTime (x2)')
