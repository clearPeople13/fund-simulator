# -*- coding: utf-8 -*-
"""费率阶梯显示改 flex+gap 布局（原 inline-block margin 视觉过挤：\"<7天 1.5%≥1年 0.5%\"）"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """.fee-wide { grid-column: 1 / -1; }
.fee-label { font-size: 12px; color: #94a3b8; display: block; margin-bottom: 4px; }
.fee-value { font-size: 13px; color: #e2e8f0; font-weight: 600; }
.fee-step { display: inline-block; margin: 2px 8px 2px 0; padding: 1px 8px; border-radius: 8px; background: rgba(99,102,241,0.12); color: #a5b4fc; font-size: 12px; }"""
new = """.fee-wide { grid-column: 1 / -1; }
.fee-label { font-size: 12px; color: #94a3b8; display: block; margin-bottom: 4px; }
.fee-value { font-size: 13px; color: #e2e8f0; font-weight: 600; }
.fee-wide .fee-value { display: flex; flex-wrap: wrap; gap: 6px; }
.fee-step { display: inline-block; padding: 1px 8px; border-radius: 8px; background: rgba(99,102,241,0.12); color: #a5b4fc; font-size: 12px; }"""
assert s.count(old) == 1, 'block not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('fee-step layout fixed')
