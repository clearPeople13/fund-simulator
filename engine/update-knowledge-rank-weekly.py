# -*- coding: utf-8 -*-
"""SYSTEM_KNOWLEDGE.md 追加第十五章：同类排名 + 周报增强"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\SYSTEM_KNOWLEDGE.md"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

s += """

***

## 十五、基金同类排名 + AI 周报增强（2026-09-19，第九批）

* **同类排名**：`GET /api/funds/:code/rank` → 全市场基金库同 fund_type 基金按 r1m/r3m/r6m/r1y 区间涨幅排序，返回该基金排名 x/y + 百分位。基金详情页新增"同类排名"卡（4 区间条形：前25% 绿 / 前60% 黄 / 尾部红 + 排名标记线）。实测 005827：近1月 4359/8522（前51%）、近1年 7601/7826（前97% 尾部）——与该基金真实表现一致。
* **周报增强**（generateReport weekly 分支新增两节）：
  - 「期间每日收益（快照口径）」：本周 portfolio_daily 逐日盈亏 + 本周合计；
  - 「AI 操盘点评」（数据驱动）：本周账户盈亏档位判断（≥100 积极 / ≥0 平稳 / ≥-100 小幅回撤 / 其余回撤明显）+ 操作汇总（买/卖笔数 + 已实现盈亏）+ 风控事件数 + 观察池规模。
* **调度加固**：scheduler/run?type=weekly|monthly 手动触发时，交易步骤（rebalanceCheck/switchFunds/dividendAdjust）包 try/catch——**非交易时段（守卫：仅工作日 09:00-15:05 可下单）触发时跳过交易、仍正常生成报告**；交易步骤返回 SKIP:原因。
* 实测：盘外触发 weekly → default rebalance 空（无操作）、aggressive SKIP 时段守卫；新周报 9/11-9/18 生成（本周合计 -195.35、AI 点评"回撤明显已按风控减仓止损"、操作 2买1卖实现 -165、观察池 28）。
"""
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('knowledge updated')
