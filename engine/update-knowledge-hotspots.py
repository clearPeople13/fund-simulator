# -*- coding: utf-8 -*-
"""SYSTEM_KNOWLEDGE.md 追加第十一章：AI 市场热点关注与分析"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\SYSTEM_KNOWLEDGE.md"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

s += """

***

## 十一、AI 市场热点关注与分析（2026-09-19 凌晨，用户点名补缺）

> 用户原话：「我们的 ai 用户有没有对热点关注并且进行分析呢，从而增加营收呢，这是应该是他该做的吧」——此前 AI 只按评分+信号选基，不关注热点，已补齐。

* **热点引擎 buildHotspots(userId)**：14 个主题词映射（医药/医疗、AI/科技、白酒/消费、半导体/芯片、新能源/光伏、军工/国防、港股/恒生、红利/价值、有色/资源、汽车/智能驾驶、农业/养殖、地产/基建、债券/固收、量化/指数增强）→ 对 fund_universe 全市场基金按基金名称聚类 → 板块平均日/周/月涨幅 + 热度分（日动能×1 + 周动能×0.4）→ 取 Top6。
* **AI 点评（按性格规则）**：日涨幅 ≥2.5% 热点爆发（激进可轻仓不追高/稳健回避）；≥1% 热点启动（激进等 BUY 信号分批/稳健看持续性）；>0 温和走强（持有跟踪）；全市场回调 热点退潮（防御）。返回 overall + comment + hotspots(含观察池/持仓关联基金)。
* **API**：`GET /api/ai/hotspots?user_id=`；**调度**：每日 close 分析（15:00）后自动跑，写 analysis_logs（analysis_type='hotspot'，signal_label=主题、signal_reason=点评）。
* **前端**：首页"🔥 市场热点 · AI 关注分析"卡（overall 徽章 + AI 点评 + 热点板块卡片：日/周/月涨幅+热度+基金数+关联基金或"AI 不盲目追热点"）；AI 决策轨迹新增 hotspot 类型（黄色"热点"标签）。
* **表结构**：analysis_logs 补 signal_label/signal_reason 列（CREATE 语句已含 + 旧库 ALTER 迁移）。
* 实测（default）：医药/医疗 日 +0.75% 周 +1.32% 热度 1.28 居首，AI 点评"温和走强，继续持有跟踪"；观察池暂无医药主题基金 → AI 不盲目追热点（行为合理）。
"""
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('knowledge updated')
