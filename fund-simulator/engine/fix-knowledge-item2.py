# -*- coding: utf-8 -*-
"""SYSTEM_KNOWLEDGE.md 修复史追加 funds 清理一条（行级匹配，容忍表格对齐空格）"""
import io, os, re

p = r"C:\Users\jiancent\WorkBuddy\fund\SYSTEM_KNOWLEDGE.md"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

lines = s.split('\n')
idx = None
for i, ln in enumerate(lines):
    if ln.startswith(u'| 09-18 | 节假日照常可交易'):
        idx = i
        break
assert idx is not None, 'fix history line not found'
add = u'| 09-18 | funds 表被 AI 扫描喂大（101 只，大量淘汰孤儿） | 清理 42 只无引用基金（funds→59），净值历史保留；基金库=universe 不受影响；定期重跑 cleanup-funds-orphans.js |'
lines.insert(idx + 1, add)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines))
print('fix history updated')
