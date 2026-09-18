# -*- coding: utf-8 -*-
"""SYSTEM_KNOWLEDGE.md：刷新第八章观察池数字 + 追加第十章查缺补漏批次记录"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\SYSTEM_KNOWLEDGE.md"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 刷新第八章观察池/订单状态
old = """* 观察池：default 28 只（25 AI + 3 手动）、aggressive 20 只（17 AI + 3 手动），两池零交集，全部带信号。"""
new = """* 观察池：default 28 只（25 AI + 3 手动）、aggressive 28 只（25 AI + 3 手动），两池零交集，全部带信号；AI 每日 09:35（盘前）+17:00（盘后）全市场重扫。"""
assert s.count(old) == 1, 'watchlist line not found'
s = s.replace(old, new)

# 追加第十章
tail = """

***

## 十、查缺补漏批次记录（2026-09-19 凌晨，持续查缺补漏按批推送）

> 铁律：每批补缺 = 功能 + 知识库/记忆 + git commit+push，全部可追溯。

### 第一批（d6546e7）— 首页对账与决策可见性
* 收益构成条（已实现 + 持仓浮动 = 累计收益，账本精确对账 -165 / -77.89 / -242.89）。
* 资产配置环形图（持仓市值 + 现金占比，import echarts 修复 window.echarts 未定义）。
* 待确认订单卡（T+1 SUBMITTED 含 AI 决策理由）。
* 修复：/api/ai/transactions 返回结构数组→{list,pending}（Object.assign 给数组附属性会被 JSON 序列化丢弃）。

### 第二批（0cb5008）— AI 经营可见性（核心：AI 经营质量可被数据观察）
* 后端 /api/ai/stats（交易笔数/已实现/卖出胜率/平均持有天数/止损止盈减仓次数/加仓再平衡次数/观察池规模/分析轮次/手续费）+ /api/ai/activity（AI 决策轨迹：交易/订单/风控/审计/分析按时间倒序）。
* 前端首页：AI 经营成绩单指标卡 + AI 决策轨迹时间线（分析 BUY/HOLD+目标/止损价、待确认订单、风控减仓）。
* 修复：audit_logs 无 user_id 列只按 target LIKE；patch-home-ai-score 误吞 .pnl-breakdown 选择器行（CSS 构建错误）。

### 第三批（422909d）— 数据可见性补全
* 后端 /api/ai/daily-pnl（账户级每日收益明细：跨基金按日聚合当日盈亏 + portfolio_daily 账户快照对照[含费口径]）+ /api/ai/fund-fees（单基金真实费率）。
* 组合页：每日收益明细表（日期|当日盈亏|账户快照对照|每只持仓基金贡献列）+ 导出 CSV（Blob，含 BOM 防 Excel 乱码）。
* 首页详情弹窗：基金信息下新增费率详情（申购/管理/托管/销售服务/赎回持有天数阶梯）。
* 修复：Portfolio.vue 无 lang=ts 的 TS 语法残留。

### 第四批（c13c686）— 数据完整性与对账口径
* 修复 saveDailySnapshot 守卫缺陷：当日买入（T+1 待确认，市值=成本）的持仓不要求当日净值公布 → default 9/18 快照补写（总资产 99804.65 / 当日 -39.32 / 现金 81851.22 / 市值 17953.43，每日盈亏图今日有数据）。
* 统一今日盈亏口径：持仓明细 市值×收益率（多乘 1+收益率 因子，005827 显示 47.77 错误）→ 份额×(今日净值-昨日净值)，与每日收益明细一致（47.54）。

### 第五批（3e259ba）— AI 决策引擎审查 + UI 细节
* 决策链路审查通过：首笔建仓（buy 20%/add 10%×市场温度）→ 持有加仓（add_cooldown_days 冷却 default 5/aggressive 3 + add_ratio 10% + 风控）→ close 全持仓退场信号（止损/止盈/趋势转空/回撤/连跌→SELL，reduce 7 天防重复）→ 再平衡（±15%）→ 换仓（周五）→ 风控（回撤熔断/集中度/总仓位）。无缺失。
* 费率阶梯 UI flex+gap 布局。
* 页面验收：FundDetail（经理/基准全）、AIAnalysis（只出建议不执行）、Alerts（风控事件：REDUCE 005827 即 9/18 AI 自动减仓卖出来源）均正常。
"""
s += tail

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('SYSTEM_KNOWLEDGE.md updated')
