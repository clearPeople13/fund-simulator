# -*- coding: utf-8 -*-
"""SYSTEM_KNOWLEDGE.md 追加第十二章：历史分红明细 + 第十三章：市场行情页"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\SYSTEM_KNOWLEDGE.md"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

s += """

***

## 十二、历史分红明细（2026-09-19 凌晨，第七批①）

* **数据源**：东财官方 fhsp API（`api.fund.eastmoney.com/f10/F10DataApi?type=fhsp`）404、HTML 页空表、acc_nav−unit_nav 全恒等——三条外部路全失败。**最终方案：本地推导**——`累计净值(acc_nav) − 单位净值(unit_nav)` 每日差值跳变 = 分红除息日，差值增量 = 每份分红。
* **清洗规则**：只保留正跳变（负跳变为拆分/折算）；跳变密度 >20% 的基金判为"复权累计净值型"（如 110005/110013 指数基金，累计净值每日复权）直接跳过。
* **结果**：28 只基金 225 条真实分红入库 dividends（fund_code/ex_date/per_unit/type='CASH'）。000001 华夏成长 25 次（2002-2025 每年分红，符合真实历史）；161725 中欧医疗健康 13 次。
* **API**：`GET /api/funds/:code/dividends?limit=`（返回 total + list）；**前端**：基金详情页新增"历史分红"卡（累计次数 + 除息日/每份分红/类型表）。

## 十三、市场行情页（2026-09-19 凌晨，第七批②）

* **数据**：benchmark_daily（沪深300 指数日线 value/change_pct）+ market_env（avg_fund_chg/bench_chg/temperature）+ fund_universe 全市场日涨跌统计。
* **API**：`GET /api/market/overview?days=90` → benchmark 走势数组 + market_env + stats（全市场涨跌家数/平均涨幅/上涨占比/近5日指数）。
* **前端**：新路由 /market（Market.vue）+ 顶栏"市场行情"菜单：市场温度徽章（热/中性/冷）、全市场统计卡（14,341 只：涨3663/跌10261/平417/占比25.5%/平均-0.23%）、近5日指数、沪深300 近90日平滑折线（渐变面积 + dataZoom + 悬浮显示点位/涨跌）。
* 实测（2026-09-18）：市场温度 neutral；指数 +0.55%；全市场平均 -0.23%。
"""
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('knowledge updated')
