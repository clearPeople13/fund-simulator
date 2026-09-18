# AI 基金自动操盘系统・运行设计规格（V3.0）

> 本文档是系统的唯一权威规格：所有功能、规则、周期、数据口径均以此为准。
> 任何代码实现与本文档冲突时，以本文档为准并同步修订。
> 版本：V3.0 ｜ 更新：2026-09-18 23:00 ｜ 适用范围：fund-simulator（
>
> 127.0.0.1:3000
>
> ，部署中心托管）
> V3.0 相对 V2.0 的变更：①AI 选基范围 = 全市场（fund_universe 14,359 只）；②观察池不设固定上限 + 每日 09:35/17:00 周期真实扫描；③AI 买入节奏真实化（盘中每 30 分钟 /pre_close/close 三周期下单，auto 参数隔离手动触发）；④trade_date 净值归属（15:00 前 T 日、之后 T+1）；⑤交易时段硬校验（仅本地工作日 09:00-15:05 可下单）+ 全链路时间显示 UTC→本地；⑥真实分批建仓（首笔 20% + 冷却期 5/3 天后按 10% 分批加仓 + 单基金上限兜底）。



***

## 0. 设计原则（不可动摇）



1. **AI 用户即基金经理**：每个用户是独立 AI 基金经理，拥有性格画像，**所有决策由性格决定**，人工不干预。

2. **只读查看**：用户只能查看，无任何手动交易 / 操作入口；AI 全自动执行；手动触发分析只出建议、永不成交。

3. **真实时间节奏**：一切按真实交易日、真实时点推进（T 日申赎、T+1 确认、净值公布节奏），**交易只发生在盘中（本地工作日 09:00-15:05）**，禁止快速 / 批量 / 跳时间 / 盘外操作。

4. **全流程周期性闭环**：系统按固定周期（盘中 / 收盘 / 盘后 / 日 / 周 / 月）自动运转：数据 → 研究 → 决策 → 执行 → 持仓 → 风控 → 绩效 → 报告。

5. **真实数据**：净值 / 估值等全部来自真实数据源（天天基金 / 新浪 ETF），禁止假数据、随机数。

6. **全链路留痕**：每次决策、每笔订单、每次风控动作都可追溯（审计日志）。

7. **文档化**：每个阶段先出设计 / 规格文档再实施，文档与代码同步；规则沉淀写入项目记忆（.workbuddy/memory）与本文档。



***

## 1. 系统全景（真实基金操作闭环）



```
&#x20;┌────────────────────────────────────────────────────────────┐

&#x20;│  周期性调度器（交易日历 + 时点触发，见 §3.2）                  │

&#x20;│  09:35 盘前扫描 → 盘中每30分钟 → 14:30 → 15:00 → 20:00      │

&#x20;│  → 21:30 净值同步 → 22:05 全市场库刷新 → 周/月任务           │

&#x20;└──────┬─────────────────────────────────────────┬───────────┘

&#x20;       ▼                                         ▼

&#x20;┌───────────────┐   ┌────────────────┐   ┌───────────────┐

&#x20;│ ① 数据层       │   │ ② 研究层        │   │ ③ 决策层       │

&#x20;│ 全市场基金库   │ → │ 观察池全市场扫描 │ → │ AI基金经理      │

&#x20;│ 真实净值/估值   │   │ 风格定位/评分   │   │ 性格画像驱动    │

&#x20;│ 费率/基准/指数  │   │ 研究报告        │   │ 信号→决策       │

&#x20;└───────────────┘   └────────────────┘   └──────┬────────┘

&#x20;                                               ▼

&#x20;┌───────────────┐   ┌────────────────┐   ┌───────────────┐

&#x20;│ ⑥ 绩效层       │   │ ⑤ 风控层        │   │ ④ 执行层       │

&#x20;│ 收益/基准/夏普  │ ← │ 止损/集中度/回撤 │ ← │ 订单引擎       │

&#x20;│ 归因/报告      │   │ 熔断/加仓冷却期  │   │ 费用/确认/到账 │

&#x20;└───────────────┘   └────────────────┘   └───────────────┘

&#x20;       └────────────── ⑦ 运营/合规/监控（横切）─────────────┘
```



***

## 2. AI 用户与性格体系（决策的唯一来源）

### 2.1 用户即 AI 基金经理

每个用户 = 一个 AI 基金经理实例，配置：id（default /aggressive/ 可扩展）、name、profile（性格画像）、initial\_capital、current\_capital、created\_at。

### 2.2 性格画像（profile）—— 决定一切

性格是一个参数集，**所有模块的规则都从它派生**：



| 参数                       | 稳健型（default）             | 激进型（aggressive）          | 说明               |
| ------------------------ | ------------------------ | ------------------------ | ---------------- |
| risk\_tolerance          | medium                   | high                     | 风险容忍度            |
| max\_position            | 60%                      | 100%                     | 总仓位上限（占可用总资产）    |
| max\_single\_fund        | 20%                      | 40%                      | 单只基金仓位上限         |
| min\_hold\_funds         | 3                        | 2                        | 最少持仓基金数（分散要求）    |
| stop\_loss               | 5%                       | 10%                      | 单基金止损线（相对成本）     |
| take\_profit             | 20%                      | 40%                      | 单基金止盈线           |
| max\_drawdown            | 10%                      | 20%                      | 组合最大回撤熔断线        |
| exit\_drawdown           | 15%                      | 25%                      | 距 60 日高点回撤触发减仓评估 |
| exit\_style              | timely（触发即减）             | patient（恶化确认 2 日才减）      | 退场风格             |
| entry\_signal\_threshold | strong（仅 buy）            | medium（buy/add 都买）       | 入场信号门槛           |
| buy\_ratio / add\_ratio  | 0.2 / 0.1                | 0.2 / 0.1                | 建仓 / 加仓比例        |
| **add\_cooldown\_days**  | **5**                    | **3**                    | **分批加仓冷却期（天）**   |
| rebalance\_frequency     | monthly                  | weekly                   | 再平衡频率            |
| watchlist\_style         | 均衡分散 / 大盘蓝筹              | 成长 / 主题 / 高弹性            | 选基偏好             |
| base\_weights            | 混合 0.5 / 股票 0.3 / 指数 0.2 | 混合 0.4 / 股票 0.5 / 指数 0.1 | 目标资产配置           |

参数可被 risk\_params 表按 user\_id 覆盖（前端只读展示）。

**性格决定的内容清单**（全部由此派生，禁止硬编码写死）：



* 观察池：选基标准（类型偏好、波动率容忍、风格、主题）

* 入场信号阈值：什么信号级别才买、买多少（buy=20% /add=10%）

* 加仓节奏：冷却期天数、加仓比例

* 退场规则：止损 / 止盈线、破位确认天数、减仓比例

* 仓位管理：单基上限、总仓位上限、建仓节奏

* 风控：回撤熔断线、集中度检查

* 再平衡：频率、触发条件

### 2.3 决策流水线（每只基金）



```
数据（净值序列/估值/日涨跌）

&#x20; → 信号引擎（趋势/均线/回撤/波动，按性格取阈值）

&#x20; → 决策引擎（按性格决定：买入比例 / 持有 / 减仓比例 / 清仓 / 换仓）

&#x20; → 风控校验（集中度、总仓位、回撤熔断、加仓冷却期；不过则拦截）

&#x20; → 生成订单（order）→ 进入执行队列（交易时段硬校验 + trade\_date 净值归属）

&#x20; → 全程写入决策日志（含理由，可追溯）
```



***

## 3. 周期性运行机制（真实时间）

### 3.1 交易日历



* 交易日 = 周一至周五（法定节假日休市）。

* 实现：isTradingWindow（本地交易日 09:00:00-15:05:59 允许下单）；节假日表 engine/holidays.json（2026 已内置，国办发明电〔2025〕7号；每年 11 月公布次年安排后补充）；收盘前/收盘/盘中分析调度非交易日自动顺延下一交易日（nextTradingDay）；holidays 表存休市日供查询审计。

* 所有 "T 日" 按真实本地日期 + 15:00 时点界定；order\_date/trade\_date 一律用本地日期（禁 UTC 日期）。

### 3.2 时点任务表（V3.0 当前节奏）



| 周期  | 时点                                   | 任务                                   | 说明                                                        |
| --- | ------------------------------------ | ------------------------------------ | --------------------------------------------------------- |
| 盘前  | 每日 09:35                             | **观察池全市场重扫**（scheduleWatchlistScan）  | AI 按性格从全市场扫描，掉队淘汰、新发现补入，不设固定上限（防御上限 MAX\_POOL=25）         |
| 盘中  | 交易时段每 30 分钟（09:30-11:30/13:00-15:00） | **实时分析 realtime（auto=true 下单）**      | 观察池信号 buy/add 且通过风控 → 立即生成订单                              |
| 收盘前 | 每日 14:30                             | **收盘前分析 pre\_close（auto=true 下单）**   | 同上                                                        |
| 收盘  | 每日 15:00                             | **收盘分析 close（auto=true）**            | 下单 + 全部持仓退场信号（止损 / 止盈 / 趋势 / 回撤）+ 账户快照 + 绩效 + 复盘 + 周 / 月报 |
| 盘后  | 每日 20:00                             | **T+1 确认 confirmPendingOrders**      | 确认 `trade_date < 今天` 的 SUBMITTED 单，成交价取 trade\_date 官方净值  |
| 盘后  | 每日 21:30                             | **净值同步**（sync-nav）                   | 拉当日真实净值入库                                                 |
| 日终  | 每日 22:05                             | **全市场基金库刷新**（sync-fund-universe，子进程） | fund\_universe 14,359 只更新                                 |
| 每周  | 周五收盘后                                | 周绩效、再平衡评估、周报                         | —                                                         |
| 每月  | 月末收盘后                                | 月绩效、归因、月报、压力测试、分红同步                  | —                                                         |

**下单纪律**：只有 AI 周期调度（realtime/pre\_close/close，auto=true）才下单；手动触发（/api/scheduler/run、/api/ai/analyze 立即分析）只出决策 / 建议，永不产生交易。order-engine createOrder 有交易时段硬校验，任何来源在非交易时段下单直接抛错。

### 3.3 申赎确认流程（真实节奏 + trade\_date 净值归属）



```
T 日 15:00 前生成订单 → trade\_date = T（按 T 日净值确认）

&#x20; → T+1 20:00 确认（该 T 日净值当晚已入库）：份额/金额落账、成交价取 trade\_date 官方净值

&#x20; → T+1 起：买入份额开始计收益；卖出份额资金到账

T 日 15:00（含）后生成的订单 → trade\_date = 下一交易日（T+1），按该日净值确认
```



* **买入**：T 日下单（净值确认）→ T+1 份额确认 → T+1 净值开始计算收益（当日买入当日无收益）。

* **卖出**：T 日下单 → T+1 确认卖出份额、资金到账；收益计算至 T 日止。

* **待确认订单**：订单状态 SUBMITTED，前端展示 "待确认"。

### 3.4 禁止行为（周期性纪律）



* **禁止非交易时段下单**：order-engine 硬校验（仅本地工作日 09:00-15:05），盘外任何来源拒单。

* 禁止一日内多次买卖（同一基金 T 日只允许 1 次下单；有未确认买单不重复）。

* 禁止跳过日期 / 批量补单 / 回填历史（除恢复备份外）。

* 非交易日禁止任何订单生成与确认。

* 数据缺失时该基金跳过决策并记录，不猜数。

* 禁止用随机数生成任何展示 / 决策数据。



***

## 4. 功能规格（按 8 环节，标注现有 / 新增）

> 状态：✅ 现有 ｜ 🔧 改造 ｜ 🆕 新增

### 4.1 数据层（运营）



| 功能                            | 状态 | 规格                                                                                                                                                                                               |
| ----------------------------- | -- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **全市场基金库（fund\_universe）**    | 🔧 | 东财 rankhandler 4 类（股票 / 混合 / 指数 / QDII）翻页，14,359 只；字段 code/name/type/unit\_nav/day\_return/r1w/r1m/r3m/r6m/r1y/ytd/nav\_date/inception\_date/scale；每日 22:05 刷新。**与观察池 / 持仓彻底独立**（AI 选基入池不进基金库展示） |
| 跟踪基金库（funds）+ 净值历史（fund\_nav） | ✅  | 每日 21:30 同步真实净值；全量历史净值（成立日起，lsjz 分页拉全）                                                                                                                                                           |
| 估值（盘中）                        | 🔧 | 新浪场内 ETF 代理（ETF\_PROXY\_MAP：161725→sh512690、005827→sz159928、000001/005267→sh510300）；fundgz 已下线保留兼容；无则回退最新公布净值（estimate\_available=false）                                                         |
| **费率表**（fund\_fees）           | ✅  | 每只基金真实费率（天天基金 jjfl\_.html，1 折口径）；新基金必须查真实费率配置，不得沿用默认                                                                                                                                             |
| 数据质量校验                        | ✅  | 净值突变 >±10% 记录并跳过决策（checkDataQuality）                                                                                                                                                             |

### 4.2 研究层（研究员）



| 功能                   | 状态 | 规格                                                                                            |
| -------------------- | -- | --------------------------------------------------------------------------------------------- |
| 基金库筛选（类型 / 关键词 / 排序） | 🔧 | 服务端分页（limit 默认 20）、sort 白名单（day\_return/r1m/r3m/r6m/r1y/unit\_nav/scale，默认 r6m 降序）            |
| 基金评分 / 风格定位          | ✅  | computeFundProfiles：近 60 日净值 → 年化波动 / 下行风险 / 风格标签 / 综合评分，每周五                                  |
| 研究报告 / 决策笔记          | ✅  | 每次分析自动写 research\_notes（信号 / 理由 / 指标 JSON），前端可读                                               |
| 宏观 / 市场环境            | ✅  | computeMarketEnv：指数涨跌 + 基金均表现 → hot/warm/neutral/cold/frozen，温度系数调节建仓 / 加仓金额（0.5/0.8/1.1/1.2） |

### 4.3 决策层（基金经理）



| 功能                   | 状态 | 规格                                                                                                                                                                                                                     |
| -------------------- | -- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **观察池 AI 自主发现（全市场）** | 🔧 | aiDiscoverWatchlist：候选 = fund\_universe 全市场；性格匹配（激进 = 股票型 / QDII / 主题 /r1y>40；稳健 = 非主题指数∪非主题 r1y<40 混合）；同策略 A/C/D 去重；跨用户去重（一只基金只归一个用户观察）；每轮先 DELETE 本用户全部 AI 项再重建（强制收敛）；MAX\_POOL=25 防御上限；09:35/17:00 周期扫描 + 启动 + 手动刷新 |
| 观察池信号（入场类）           | ✅  | getFundSignal/buildWatchSignal：buy 分批建仓 /add 轻仓试探 /watch 回踩再入 /wait 暂缓入场（20 日趋势 + 60 日回撤 + MA20）                                                                                                                       |
| **分批建仓与分批加仓**        | 🔧 | 未持有：buy 20%/add 10% 首笔建仓；已持有且信号仍 buy/add：冷却期（稳健 5 天 / 激进 3 天）后按 add\_ratio 10% 分批加仓，单基金上限兜底                                                                                                                            |
| 退场决策                 | ✅  | buildExitSignal：止损 / 止盈 / 趋势转空 / 回撤过大 / 连跌 → sell/reduce/hold，按 exit\_style 差异化；趋势 reduce 每 7 日限一次；close 且 auto 时执行                                                                                                    |
| 换仓决策                 | ✅  | switchFunds（观察池强信号 vs 持仓弱信号，卖弱买强等额，周五评估，受风控约束）                                                                                                                                                                         |
| 再平衡                  | ✅  | rebalanceCheck（类型配置偏离 >15% 生成调仓订单，按性格频率）                                                                                                                                                                               |
| 定投 / 定期计划            | ⬜  | 可选，未实施                                                                                                                                                                                                                 |

### 4.4 执行层（交易员）



| 功能           | 状态 | 规格                                                                                                                                         |
| ------------ | -- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 订单引擎（orders） | 🔧 | 状态机 CREATED → SUBMITTED → DONE / CANCELLED；**订单表含 trade\_date 列（确认净值日）**；下单时机 realtime/pre\_close/close（auto=true）                         |
| **交易时段硬校验**  | 🆕 | createOrder 仅本地工作日 09:00-15:05 允许；15:00 后提交按 T+1（trade\_date = 次日）                                                                         |
| **手动触发隔离**   | 🆕 | performAnalysis (analysisType, auto=false) 默认不下单；手动 /api/scheduler/run、/api/ai/analyze 只出建议                                                |
| 费用计算         | ✅  | 申购费内扣法（前端扣除计入成本）；赎回费 FIFO 分批（每批按各自持有天数查阶梯）；管理 / 托管 / 销售服务费年化逐日计提                                                                           |
| T+1 确认       | 🔧 | confirmPendingOrders：只确认 `trade_date < 今天` 的 SUBMITTED 单；成交价取 trade\_date 官方净值（无则回退下单快照）；确认写 transactions + holdings + realized\_pnl（SELL） |
| 撤单 / 调整      | ✅  | cancelOrder 仅 SUBMITTED 且当日可撤                                                                                                              |

### 4.5 风控层（风控）



| 功能          | 状态 | 规格                                                                |
| ----------- | -- | ----------------------------------------------------------------- |
| 止损 / 止盈触发引擎 | ✅  | 每日收盘决策前检查全部持仓，按性格参数触发减仓 / 清仓                                      |
| 仓位集中度       | ✅  | 下单前：单基 ≤ max\_single\_fund、总仓位 ≤ max\_position；违反拦截记 BUY\_BLOCKED |
| **加仓冷却期**   | 🆕 | 距上次确认买入 ≥ add\_cooldown\_days（5/3 天）才允许加仓                         |
| 组合风险指标      | ✅  | 波动率（年化）、最大回撤、夏普比率，每日快照计算                                          |
| 回撤熔断        | ✅  | 组合回撤 > max\_drawdown：暂停新买入，仅允许减仓，直至恢复                             |
| 压力测试        | ✅  | 月度：-10%/-20% 情景回撤报告                                               |
| 净值异动预警      | ✅  | 单日净值跌 >5%（稳健）/8%（激进）自动告警并进入减仓评估                                   |

### 4.6 绩效层（绩效分析）



| 功能              | 状态 | 规格                                  |
| --------------- | -- | ----------------------------------- |
| 每日盈亏 / 资产走势     | ✅  | portfolio\_daily 快照，T+1 感知          |
| 累计 / 区间收益       | ✅  | 时间加权口径                              |
| 基准对比            | ✅  | 沪深 300 真实收盘（东方财富 push2his），超额收益     |
| 夏普 / 波动率 / 最大回撤 | ✅  | 每日计算                                |
| 业绩归因            | ✅  | 简化 Brinson：配置贡献 vs 选基贡献，月末          |
| 周报 / 月报         | ✅  | reports 表，周五 + 月末收盘自动生成；报告正文时间全部本地化 |

### 4.7 运营 / 合规 / 监控



| 功能       | 状态 | 规格                                                                    |
| -------- | -- | --------------------------------------------------------------------- |
| 真实数据定时更新 | ✅  | 21:30 净值、22:05 全市场库                                                   |
| 数据库备份    | ✅  | backup-db.js + Windows 计划任务 FundSimulator-DB-Backup（每日 21:00，保留 30 份） |
| 审计日志     | ✅  | audit\_logs：所有决策 / 订单 / 风控 / 调度动作                                     |
| 权限分级     | ✅  | 系统只读；写操作仅调度器 / 内部调用                                                   |
| 监控预警中心   | ✅  | risk\_events + data\_quality 聚合，前端 "预警" 页                             |
| 每日复盘摘要   | ✅  | generateDailyRecap（市场 / 账户 / 操作 / 事件 / 明日关注），每日收盘                     |



***

## 5. 数据模型

### 5.1 核心表



| 表                  | 用途                       | 关键字段                                                                                                                                                                                    |
| ------------------ | ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| fund\_universe     | 全市场基金库                   | code, name, type (粗类), unit\_nav, day\_return, r1w/r1m/r3m/r6m/r1y, nav\_date, inception\_date, scale (不可靠勿展示), updated\_at                                                             |
| funds              | 跟踪库（AI 入池 / 手动添加 / 持仓基金） | code, name, type, manager, inception\_date, benchmark, updated\_at                                                                                                                      |
| fund\_nav          | 净值历史                     | fund\_code, nav\_date, unit\_nav, daily\_return                                                                                                                                         |
| watchlist          | 观察池                      | user\_id, fund\_code, reason, source('ai'/'manual'), created\_at                                                                                                                        |
| orders             | 订单                       | id, user\_id, fund\_code, order\_type(BUY/SELL), amount, shares, price, fee, status(SUBMITTED/DONE/CANCELLED), **order\_date, trade\_date (确认净值日)**, reason, created\_at, confirm\_date |
| holdings           | 持仓                       | user\_id, fund\_code, shares, cost, total\_cost                                                                                                                                         |
| transactions       | 交易流水（确认后）                | user\_id, fund\_code, transaction\_type, amount, price, shares, fees, reason, **remaining\_shares (FIFO 可赎份额)**, transaction\_date                                                      |
| realized\_pnl      | 已实现盈亏账本                  | user\_id, fund\_code, amount, sell\_fee, note (FIFO 明细)                                                                                                                                 |
| portfolio\_daily   | 每日账户快照                   | user\_id, date, total\_assets, daily\_pnl, cash, market\_value                                                                                                                          |
| fund\_fees         | 真实费率表                    | fund\_code, buy\_fee\_pct, sell\_fee\_rules (JSON 阶梯), manage\_fee\_pct, custody\_fee\_pct, service\_fee\_pct                                                                           |
| benchmark\_daily   | 基准指数                     | date, close（沪深 300 真实收盘）                                                                                                                                                                |
| performance\_daily | 每日绩效                     | user\_id, date, total\_return, benchmark\_return, excess, volatility, sharpe, max\_drawdown                                                                                             |
| risk\_events       | 风控事件                     | user\_id, event\_type(STOP\_LOSS/REDUCE/BUY\_BLOCKED/DRAWDOWN/...), fund\_code, detail, action, created\_at                                                                             |
| risk\_params       | 性格参数覆盖                   | user\_id, param\_name, param\_value                                                                                                                                                     |
| market\_env        | 市场温度                     | date, temperature(hot/warm/neutral/cold/frozen)                                                                                                                                         |
| reports            | 报告                       | user\_id, report\_type, period, content, created\_at                                                                                                                                    |
| research\_notes    | 研究笔记                     | user\_id, fund\_code, analysis\_type, signal, reason, metrics(JSON)                                                                                                                     |
| fund\_profiles     | 基金评分 / 风格                | fund\_code, volatility, downside\_risk, style\_label, score                                                                                                                             |
| analysis\_logs     | 分析日志                     | user\_id, analysis\_type, fund\_code, decision, confidence, entry\_price, target\_price, stop\_loss, ...                                                                                |
| audit\_logs        | 审计日志                     | ts, actor, action, target, params(JSON), result                                                                                                                                         |
| scheduler\_runs    | 调度运行记录                   | run\_type, started\_at, finished\_at, status, summary                                                                                                                                   |

### 5.2 时间存储约定（重要）



* SQLite CURRENT\_TIMESTAMP /created\_at 存 **UTC**（无时区标记）；**显示层统一按 UTC 解析转本地**（Home/Alerts/Reports 均已实现 formatDate/formatTime）；报告正文时间用 utcToLocalStr。

* order\_date /trade\_date 一律**本地日期**（getLocalDateStr）。

* 前端时间展示：无时区标记的字符串按 UTC 解析 +8 转本地；带 Z / 偏移的 ISO 原样解析。



***

## 6. 关键口径（费用与收益）

### 6.1 收益口径



* 组合收益：时间加权（修正 Dietz），每日绩效 = 当日盈亏 / 期初净值资产。

* 持仓收益：`(现价 - 成本) / 成本`，T+1 起计入当日涨跌（当日买入当日无收益）。

* 基准：沪深 300 指数（真实收盘），超额 = 组合收益 − 基准收益。

### 6.2 费用口径（真实基金规则，2026-09-18 校准）

**费率来源**：天天基金各基金费率页（[fundf10.eastmoney.com/jjfl\_](https://fundf10.eastmoney.com/jjfl_).html），按基金单独配置 fund\_fees 表 /fee.js FUND\_FEES；新基金必须查真实费率，不得沿用默认。



| 基金                    | 申购费 (1 折) | 赎回阶梯                                                             | 管理 / 托管      |
| --------------------- | --------- | ---------------------------------------------------------------- | ------------ |
| 005827 易方达蓝筹精选混合      | 0.15%     | <7d 1.5% / 7-29d 0.75% / 30-364d 0.5% / 365-729d 0.25% / ≥730d 0 | 1.2% / 0.2%  |
| 161725 招商中证白酒 (LOF) A | 0.10%     | <7d 1.5% / 7-364d 0.5% / ≥365d 0.25%                             | 1.0% / 0.22% |
| 000001 华夏成长混合         | 0.15%     | <7d 1.5% / ≥7d 0.5%                                              | 1.2% / 0.2%  |
| 005267 嘉实价值精选股票 A     | 0.15%     | <7d 1.5% / 7-29d 0.75% / 30-364d 0.5% / 365-729d 0.25% / ≥730d 0 | 1.2% / 0.2%  |



| 费用              | 规则                                                                         | 记账         |
| --------------- | -------------------------------------------------------------------------- | ---------- |
| 申购费             | 前端收费，**内扣法**：申购费 = 金额 − 金额 /(1 + 费率)；净申购额 = 金额 /(1 + 费率)；份额 = 净额 / 净值      | 申购费计入持仓成本  |
| 赎回费             | **先进先出（FIFO）分批**：从最早买入批次扣减，每批按各自持有天数查该基金阶梯，赎回费 = Σ(批金额 × 批费率)；持有天数从各批买入日起算 | 卖出时从到账金额扣除 |
| 管理 / 托管 / 销售服务费 | 年化（按 fund\_fees）逐日计提                                                       | 每日从该基金市值计提 |



* 卖出成本按批次含费成本价（amount/shares）累计；已实现盈亏 = 赎回净额 − 卖出成本。

* transactions.remaining\_shares 记录每笔 BUY 剩余可赎份额；FIFO 明细写入 realized\_pnl.note。



***

## 7. API 设计（现状）



```
GET  /api/funds?type=\&keyword=\&sort=\&page=\&limit=      # 全市场基金库（服务端分页，universe）

GET  /api/funds/:code                                  # 基金详情（funds 优先，universe 兜底 tracked:false）

GET  /api/funds/:code/nav                               # 净值序列

GET  /api/funds/:code/returns                           # 各区间涨跌幅（支付宝式）

GET  /api/funds/:code/profile /research                 # 评分/研究笔记

GET  /api/users/:id/portfolio /holdings /orders /transactions /watchlist /daily

POST /api/users/:id/watchlist                           # 手动添加自选（全市场可用）

DELETE /api/users/:id/watchlist/:code                   # 取消自选

GET  /api/portfolio/estimates?codes=                    # 批量盘中估值（ETF 代理）

GET  /api/ai/status /daily /portfolio

POST /api/ai/analyze                                    # 立即分析（只出建议，不成交）

POST /api/ai/discover-watchlist                         # 手动触发 AI 全市场选基

GET  /api/risk/events /api/risk/params/:user\_id

GET  /api/performance/:user\_id /api/benchmark /api/reports /api/alerts /api/market-env /api/daily-recap

POST /api/scheduler/run?type=                           # 手动触发周期（本机调试；只出决策不下单）
```

所有写接口仅调度器 / 内部调用可执行；前端一律只读。



***

## 8. 前端规划（Ant Design Vue v4，深色金融科技风）



| 页面               | 路由           | 内容                                                                                                           |
| ---------------- | ------------ | ------------------------------------------------------------------------------------------------------------ |
| 首页 Home          | /            | 账户总览、资产 / 盈亏走势（真实快照）、观察池（信号卡、AI / 手动标签、取消）、交易记录（手续费列、T+1 待确认）、持仓明细（预估今日 ETF 估值、详情弹窗 = 收益走势折线图 + 买卖节点 + 基金信息） |
| 基金库 Funds        | /funds       | 全市场 14,359 只、服务端分页、类型筛选、排序、☆ 观察                                                                              |
| 基金详情 FundDetail  | /funds/:code | 净值走势、涨跌幅区间条形图（支付宝式）、基金信息、跟踪提示                                                                                |
| 投资组合 Portfolio   | /portfolio   | 持仓明细、资产配置饼图                                                                                                  |
| 投资分析 Analysis    | /analysis    | 收益 / 风险 / 资产配置 / 交易统计 4 tab                                                                                  |
| AI 分析 AIAnalysis | /ai-analysis | 单基金信号分析（入场 / 目标 / 止损 / 理由）                                                                                   |
| 预警中心 Alerts      | /alerts      | 风控事件 + 数据质量聚合（时间本地化）                                                                                         |
| 报告中心 Reports     | /reports     | 每日复盘 / 周报 / 月报 / 压力测试 + Markdown 渲染（时间本地化）                                                                   |
| 基金经理 Profile     | /profile     | 两用户性格参数只读展示                                                                                                  |

统一：ant-design-vue 4.2.6 + vue 3.6 + echarts 6.1 + axios；深色 token（bg #131a35 /card #1c2348 / 主色 #6366f1）；宽度恒定 1040；斑马纹 / 分页已深色适配。



***

## 9. 分阶段实施记录

### 阶段 P0-1：周期调度 + 订单执行引擎（地基）【已完成 2026-09-18】

scheduler 模块（close 15:00 /confirm 20:00 + 启动恢复）、orders 状态机 + T+1 确认、费用模型（engine/fee.js）、审计日志。

### 阶段 P0-2：退场 + 风控引擎【已完成 2026-09-18】

buildExitSignal（按性格）、checkRiskControls（回撤熔断 / 集中度 / 总仓位）、risk\_params 落库、防重复（reduce 7 日限一次、pendingBuy 防重）。

### 阶段 P0-3：绩效与报告【已完成 2026-09-18】

沪深 300 真实基准、performance\_daily、周报 / 月报、报告 API。

### 阶段 P1：决策质量【已完成 2026-09-18】

基金评分 / 风格、研究笔记、市场温度、换仓、再平衡、分红、归因、压力测试、数据质量校验、每日复盘。

### 阶段 P2：体验与扩展【已完成 2026-09-18】

预警中心、报告中心、基金经理画像、数据质量告警。

### 阶段 P3：全市场与真实化改造【已完成 2026-09-18 晚】



* [x] AI 选基范围 = 全市场（sync-fund-universe 14,359 只 + aiDiscoverWatchlist 全市场性格匹配）

* [x] 基金库 = 全市场（与观察池独立，服务端分页）

* [x] 观察池不设固定上限 + 每日 09:35/17:00 周期扫描（MAX\_POOL=25 防御）

* [x] AI 买入节奏真实化（盘中 30 分钟 /pre\_close/close 三周期 auto=true 下单 + 手动触发隔离）

* [x] trade\_date 净值归属（orders 表迁移）

* [x] 交易时段硬校验（09:00-15:05）+ 全链路时间本地化

* [x] 真实分批建仓（首笔 20% + 冷却期 5/3 天 + 10% 分批加仓 + 单基金上限兜底）

**每个阶段完成后：更新本文档状态 → 部署中心重启 → 浏览器验收 → 写入项目记忆。**



***

## 10. 文档体系



| 文档      | 位置                                                                       | 用途                               |
| ------- | ------------------------------------------------------------------------ | -------------------------------- |
| 本文档     | fund/AI\_FUND\_OPERATIONS\_DESIGN.md                                     | 总规格（权威，V3.0）                     |
| 系统知识库   | fund/SYSTEM\_KNOWLEDGE.md                                                | 全部沉淀规则 / 口径 / 缺陷修复史 / 工程约定（规则速查） |
| 项目记忆    | fund/.workbuddy/memory/\*.md                                             | 每日进展 / 决策记录（明细）                  |
| 需求 / 计划 | fund/fund-simulator/REQUIREMENTS.md / PROJECT\_PLAN.md / SYSTEM\_PLAN.md | 早期规划                             |
| 迁移记录    | fund/fund-simulator/artifacts/migration-notes.md                         | Element Plus→AntD 组件映射           |