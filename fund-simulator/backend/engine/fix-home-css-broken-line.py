# -*- coding: utf-8 -*-
"""修复 patch-home-ai-score 吞掉的 .pnl-breakdown 选择器行"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """ flex-wrap: wrap; gap: 12px; margin: 14px 0 4px; }"""
new = """.pnl-breakdown { display: flex; flex-wrap: wrap; gap: 12px; margin: 14px 0 4px; }"""
assert s.count(old) == 1, 'broken line not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Home.vue fixed')
