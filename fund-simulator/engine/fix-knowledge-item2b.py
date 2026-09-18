# -*- coding: utf-8 -*-
"""SYSTEM_KNOWLEDGE.md §9 第 2 项标记完成"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\SYSTEM_KNOWLEDGE.md"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old2 = u"2. funds 表历史 AI 新入的～20 只基金未清理（基金库已改查 universe，funds 仅剩跟踪 / 交易用途，是否清理待用户意见）。"
new2 = u"2. ~~funds 表历史 AI 新入的基金未清理~~ **已完成（2026-09-18）**：清理 42 只无引用孤儿（funds 101→59；不在 watchlist/holdings/orders/transactions/fund_fees 的行），真实净值历史保留（62509 条，重新入库可复用）；清理脚本 `fund-simulator\\cleanup-funds-orphans.js`；基金库页面不受影响（查 universe）。注：AI 扫描仍会持续入库新基金，观察池淘汰后 funds 行会再积累，定期重跑该脚本即可。"
assert s.count(old2) == 1, 'item2 not found'
s = s.replace(old2, new2)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('item2 done')
