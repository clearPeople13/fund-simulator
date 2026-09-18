# -*- coding: utf-8 -*-
"""SYSTEM_KNOWLEDGE.md 修复史追加累计收益 bug 修复"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\SYSTEM_KNOWLEDGE.md"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

oldfix = u"| 09-18 | 归因结果不写入月报正文（仅 API 返回） | generateReport 月报追加\"业绩归因（简化 Brinson）\"小节（配置/选基/总超额） |"
newfix = oldfix + u"\n| 09-18 | 累计收益恒 0（总资产=现金+持仓成本，非市值） | /api/ai/portfolio 补 latest_nav/market_value/today_pnl，total_assets 改市值口径；Home.vue 卡片改用后端市值与快照盈亏 |"
assert s.count(oldfix) == 1, 'fix line not found'
s = s.replace(oldfix, newfix)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('knowledge updated')
