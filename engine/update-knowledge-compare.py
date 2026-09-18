# -*- coding: utf-8 -*-
"""SYSTEM_KNOWLEDGE.md 追加第十六章：双 AI 基金经理经营对比"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\SYSTEM_KNOWLEDGE.md"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

s += """

***

## 十六、双 AI 基金经理经营对比（2026-09-19，第十批）

* **API**：`GET /api/ai/compare` → users（default/aggressive 两账户：总资产/累计收益额与率/现金/持仓市值/已实现盈亏/费用/交易数/观察池/持仓数）+ daily（每日总资产双序列对齐）+ holdings（两账户持仓并排）。
* **前端**：首页新增"🤝 双 AI 基金经理经营对比"卡——两用户并排指标卡（绿=稳健/黄=激进）+ 每日资产双线图（ECharts）。
* 实测：稳健 +0.02%（¥100,020.72，已实现 -165，费用 191.93，3笔/28只）；激进 -0.09%（¥99,907.32，已实现 0，费用 43.94，2笔/28只）。同本金 10 万起步。
* 盘中估值（fundgz.1234567.com.cn/js/xxx.js）试测失败：东财系接口全部"页面未找到"（网络屏蔽），估值功能无数据源不实施、不编造。
"""
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('knowledge updated')
