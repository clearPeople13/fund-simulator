# -*- coding: utf-8 -*-
"""SYSTEM_KNOWLEDGE.md 追加第十四章：账户 vs 基准 + 收益日历"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\SYSTEM_KNOWLEDGE.md"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

s += """

***

## 十四、账户 vs 基准对比 + 收益日历（2026-09-19，第八批）

* **对比曲线**：`GET /api/ai/performance-vs-benchmark?user_id=` → 账户累计收益率（portfolio_daily.total_assets / initial_capital − 1）与沪深300 累计涨幅（benchmark_daily.value 首日归一化）双序列对齐。组合页"📊 账户累计收益 vs 沪深300"双线图（绿实线=AI账户、黄虚线=沪深300），直观看出 AI 相对指数的超额表现。
* **收益日历**：组合页"🗓 收益日历（近3个月）"，按日网格热力（涨绿/跌红/持平/无数据灰，悬浮显示日期+盈亏金额），数据口径 = 持仓份额 × 净值变动（与每日收益明细同源）。
* 实测（default，2026-09-18）：9/16 -126、9/17 +48（份额口径；账户快照口径 9/16 -156.03、9/17 -39.32 已在每日收益明细列对照显示）。
* 注意：系统全局配色为涨绿跌红（.profit=绿 .loss=红），与 A 股红涨绿跌惯例相反，但全系统统一，文案已对齐。
"""
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('knowledge updated')
