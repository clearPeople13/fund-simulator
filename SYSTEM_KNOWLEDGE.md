# 基金模拟交易系统・系统知识库

> 本文件是系统的
>
> **规则速查知识库**
>
> ：沉淀全部业务口径、操作规则、缺陷修复史与工程约定。
> 与权威规格 
>
> `AI_FUND_OPERATIONS_DESIGN.md`
>
> （V3.0）配套；每日明细见 
>
> `.workbuddy/memory/2026-09-17.md`
>
>  与 
>
> `2026-09-18.md`
>
> 。
> 更新：2026-09-18 23:00 ｜ 应用：fund-simulator（127.0.0.1:3000，部署中心 127.0.0.1:8900 托管）

> **工程约定（git 版本管理）**：项目已纳入 git（仓库根 = 本目录，首次提交 228a808）。
> 铁律：**任何规则/口径调整、缺陷修复、功能改动，必须同步更新本文档与 `.workbuddy/memory/`，
> 并连同代码一起 `git add -A && git commit`**，保证换环境 clone 后可无缝继续。
> 新环境运行见根目录 `README.md`；依赖/构建产物不入库（.gitignore），数据库（含账目/净值/观察池）入库。



***

## 一、系统定位与铁律



1. **AI 用户即基金经理**：default（稳健）/aggressive（激进）两个 AI 基金经理，全部决策由性格画像决定，人工零干预。

2. **用户全程只读**：无任何手动交易入口；"立即分析" 只出建议、永不成交；手动跑调度任务也只出决策。

3. **交易只在盘中**：订单只能由 AI 周期调度（realtime/pre\_close/close，auto=true）在**本地工作日 09:00-15:05** 生成；order-engine 有硬校验，盘外任何来源直接拒单。

4. **真实时间节奏**：T 日申赎、T+1 确认、15:00 净值分界、21:30 净值同步、22:05 全市场库刷新。

5. **真实数据**：净值 / 估值 / 费率 / 基准全部来自真实源（天天基金、新浪 ETF、东方财富），**全系统无随机数**。

6. **全链路留痕**：audit\_logs /risk\_events/analysis\_logs /scheduler\_runs 可追溯。



***

## 二、AI 操盘规则（核心）

### 2.1 AI 选基（观察池主力来源）



* 候选范围：**全市场基金库 fund\_universe（14,359 只）**，与 "基金库页面" 独立。

* 性格匹配：


  * 激进型 = 股票型 | QDII | 行业主题（新能源 / 白酒 / 能源 / 科技 / 军工 / 医药 / 半导体 / 芯片 / 数字 / 人工智能 / 互联网…）| r1y>40%

  * 稳健型 = 非主题指数型 ∪ 非主题且 r1y<40% 的混合型

* 过滤：unit\_nav>0、规模≥2 亿、成立满 1 年、净值≥30 条（宁缺毋滥）；同策略 A/C/D 去重（留评分最高）；**跨用户去重**（一只基金只归一个用户观察）。

* 每轮：先 DELETE 本用户全部 AI 项 → 按全市场排名重建 → 掉队自动淘汰、新发现补入。

* 评分：激进 = 0.5・max (r1y,0)+0.6・max (r3m,0)+1.2・max (day,0)+ 主题 3 + 股票型 2 + 超跌反弹；稳健 = 0.5・max (r1y,0)+0.3・max (r6m,0)+0.3・max (day,0)+ 趋势加分 + 回撤惩罚 + 指数型 6。

* **观察池不设固定上限**（防御上限 MAX\_POOL=25）；手动添加不限量、永不自动删除。

* 触发时机：每日 09:35 盘前 + 17:00 盘后自动重扫、服务启动时、手动 "刷新 AI 推荐"/POST/api/ai/discover-watchlist。discoverLock 防并发。

### 2.2 观察池信号（真实净值驱动）



* buy 分批建仓（趋势向上 + 回调≥8%+ 站上 20 日线）/add 轻仓试探（趋势弱但站上 20 日线）/watch 回踩再入 /wait 暂缓入场。

* 指标：5 日 / 20 日涨跌、距 60 日高点回撤、MA20 位置。每条信号带一句话理由。

### 2.3 买入（分批建仓语义）



* **首笔建仓（未持有）**：buy → 可用资金 ×20%；add → 可用资金 ×10%；再 × 市场温度系数（frozen 0.5/cold 0.8/warm 1.1/hot 1.2）；<¥100 跳过。

* **分批加仓（已持有，信号仍 buy/add）**：可用资金 ×10%× 温度系数；**冷却期**：距上次确认买入 ≥ 5 天（稳健）/3 天（激进）才可加仓；单基金市值 ≤ max\_single\_fund（20%/40%）、总仓位 ≤ max\_position（60%/100%）由 checkRiskControls 兜底拦截。

* 下单前检查：pendingBuy（已有待确认买单不重复）、回撤熔断（组合回撤 ≥ 熔断线暂停新买入）。

### 2.4 退场（close 且 auto=true 时执行）



* buildExitSignal：止损（-5%/-10%）、止盈（+20%/+40%）、趋势转空（近 20 日跌 + 破 20 日线）、回撤过大（距 60 日高点 15%/25%）、连跌 → sell（清仓）/reduce（减 50%）/hold。

* 风格差异：稳健 = 触发即减；激进 = 恶化确认（连续 2 日）才减。趋势 reduce 每 7 日最多一次。

* SELL 确认走 FIFO 分批赎回 + 每批持有天数阶梯费率。

### 2.5 订单与净值归属



* **15:00 前**下单 → trade\_date = 当日（T 日净值确认）；**15:00 后**下单 → trade\_date = 次日（T+1）。

* 20:00 确认 `trade_date < 今天` 的 SUBMITTED 单；成交价取 trade\_date 官方净值（无则回退下单快照）。

* 手动触发（scheduler/run、立即分析）**永远不产生订单**。

### 2.6 AI 每日节奏总表



| 时点        | 动作                                         |
| --------- | ------------------------------------------ |
| 09:35     | 观察池全市场重扫（性格选基，淘汰 / 补入）                     |
| 盘中每 30 分钟 | 实时分析：观察池信号强 → 自动下单（auto=true）              |
| 14:30     | 收盘前分析：自动下单                                 |
| 15:00     | 收盘分析：下单 + 全部持仓退场评估 + 快照 + 绩效 + 复盘 + 周 / 月报 |
| 20:00     | T+1 确认（trade\_date 已到期的订单按官方净值落账）          |
| 21:30     | 当日真实净值同步入库                                 |
| 22:05     | 全市场基金库刷新（子进程）                              |



***

## 三、数据与费用口径

### 3.1 时间口径（重要）



* 数据库时间存储：SQLite CURRENT\_TIMESTAMP /created\_at 存 **UTC**（无时区标记）。

* 显示层：**一律按 UTC 解析转本地**（Home formatDate / Alerts・Reports formatTime / 报告正文 utcToLocalStr）。

* order\_date / trade\_date：**本地日期**（getLocalDateStr），禁用 UTC 日期。

* 前端解析规则：`YYYY-MM-DD HH:mm:ss` 无时区标记 → 按 UTC（补 Z）转本地；带 Z / 偏移 → 原样解析。

* **交易日历**：交易日 = 周一～周五 且 非法定节假日；休市日数据在 `engine/holidays.json`（按年份分组，来源国务院办公厅通知，每年 11 月公布次年安排后补充）；调休上班的周末（如 1/4、2/14、9/20、10/10）A 股不开市，无需列入。


  * 2026 休市日（19 个工作日节假日）：01-01/01-02（元旦）、02-16\~02-20/02-23（春节）、04-06（清明）、05-01/05-04/05-05（劳动节）、06-19（端午）、09-25（中秋）、10-01/10-02/10-05\~10-07（国庆）。

  * order-engine.js `isTradingWindow` = isTradingDay && 09:00-15:05（节假日盘中下单被硬拒）；server.js 收盘前 / 收盘 / 盘中分析调度**非交易日自动顺延到下一交易日**（nextTradingDay）。

  * holidays 表（date/name）存 2026 休市日，启动幂等 seed，供审计 / 查询。

### 3.2 净值与估值



* 净值：天天基金 lsjz 接口，每日 21:30 增量同步；全量历史从成立日拉取（单页 20 条分页）。

* 盘中估值：新浪场内 ETF 代理（ETF\_PROXY\_MAP：161725→sh512690 酒 ETF、005827→sz159928 消费 ETF、000001/005267→sh510300 沪深 300ETF）；fundgz 已下线保留兼容；无代理 → 回退最新公布净值（estimate\_available=false）。

* 数据质量：净值突变 >±10% 记录 data\_quality 并跳过该基金决策，不猜数。

### 3.3 费率（真实基金，1 折口径）



| 基金     | 申购费   | 赎回阶梯                                                             | 管理 / 托管      |
| ------ | ----- | ---------------------------------------------------------------- | ------------ |
| 005827 | 0.15% | <7d 1.5% / 7-29d 0.75% / 30-364d 0.5% / 365-729d 0.25% / ≥730d 0 | 1.2% / 0.2%  |
| 161725 | 0.10% | <7d 1.5% / 7-364d 0.5% / ≥365d 0.25%                             | 1.0% / 0.22% |
| 000001 | 0.15% | <7d 1.5% / ≥7d 0.5%                                              | 1.2% / 0.2%  |
| 005267 | 0.15% | <7d 1.5% / 7-29d 0.75% / 30-364d 0.5% / 365-729d 0.25% / ≥730d 0 | 1.2% / 0.2%  |



* 申购费**内扣法**：费 = 金额−金额 /(1 + 费率)；净额 = 金额 /(1 + 费率)；份额 = 净额 / 净值；费计入持仓成本。

* 赎回费 **FIFO 分批**：从最早买入批次扣减，每批按各自持有天数查阶梯；持有天数从各批买入日算；FIFO 明细入 realized\_pnl.note。

* **新基金费率必须查天天基金 jjfl\_.html 配置，不得沿用默认**。

### 3.4 收益口径



* 当日买入当日无收益（T+1）；持仓累计盈亏 = 市值 − 成本（T+1 待确认时显示待确认态）。

* 已实现盈亏 = 赎回净额 − 卖出含费成本；realized\_pnl 账本保证现金一致（现金 = 初始 − Σ 成本 + Σ 已实现盈亏）。

* 基准：沪深 300 真实收盘；超额 = 组合收益 − 基准收益。



***

## 四、数据表速查



| 表                                                                                           | 用途                          | 关键字段                                                                                    |
| ------------------------------------------------------------------------------------------- | --------------------------- | --------------------------------------------------------------------------------------- |
| fund\_universe                                                                              | 全市场基金库（14,359）              | code/name/type/unit\_nav/day\_return/r1m/r3m/r6m/r1y/inception\_date/scale\*（\* 不可靠勿展示） |
| funds                                                                                       | 跟踪库                         | 含 manager/inception\_date/benchmark（f10 已补 4 只）                                         |
| fund\_nav                                                                                   | 净值历史                        | fund\_code/nav\_date/unit\_nav/daily\_return                                            |
| watchlist                                                                                   | 观察池                         | user\_id/fund\_code/reason/**source(ai/manual)**                                        |
| orders                                                                                      | 订单                          | status(SUBMITTED/DONE/CANCELLED)/**order\_date/trade\_date**/fee                        |
| transactions                                                                                | 交易流水                        | transaction\_type/amount/price/shares/fees/**remaining\_shares**                        |
| holdings                                                                                    | 持仓                          | shares/cost/total\_cost                                                                 |
| realized\_pnl                                                                               | 已实现盈亏                       | amount/sell\_fee/note (FIFO 明细)                                                         |
| portfolio\_daily                                                                            | 每日快照                        | total\_assets/daily\_pnl/cash/market\_value                                             |
| fund\_fees                                                                                  | 真实费率                        | buy\_fee\_pct/sell\_fee\_rules(JSON)/manage/custody/service                             |
| benchmark\_daily                                                                            | 沪深 300                      | date/close                                                                              |
| performance\_daily                                                                          | 绩效                          | total\_return/benchmark\_return/excess/volatility/sharpe/max\_drawdown                  |
| risk\_events                                                                                | 风控事件                        | event\_type(STOP\_LOSS/REDUCE/BUY\_BLOCKED/DRAWDOWN)                                    |
| risk\_params                                                                                | 性格覆盖                        | param\_name/param\_value                                                                |
| market\_env                                                                                 | 市场温度                        | temperature                                                                             |
| reports / research\_notes / fund\_profiles / analysis\_logs / audit\_logs / scheduler\_runs | 报告 / 笔记 / 评分 / 分析 / 审计 / 调度 | —                                                                                       |



***

## 五、前端与部署



* 技术栈：Vue 3.6 + Vite + **Ant Design Vue 4.2.6**（Element Plus 已卸载）+ ECharts 6.1 + axios；深色金融科技风（bg #131a35 /card #1c2348 / 主色 #6366f1）；内容宽度恒定 1040。

* 页面：/（首页）、/funds（全市场基金库）、/funds/:code（详情）、/portfolio、/analysis、/ai-analysis、/alerts、/reports、/profile。

* 构建：**必须&#x20;**`cd fund-simulator\frontend && npm run build`（根目录无 build 脚本）；产物 dist/assets/\*.js；浏览器强刷 `?t=<时间戳>`。

* 运行：node server.js（部署中心托管，端口 3000）；重启走 POST [http://127.0.0.1:8900/api/services/fund-simulator/restart](http://127.0.0.1:8900/api/services/fund-simulator/restart)；日志 `C:\Users\jiancent\deploy-center\logs\fund-simulator.log`（会被净值同步刷屏，读取需过滤）。

* 数据库：`fund_simulator\fund_simulator.db`（sqlite3；engine 目录下验证脚本须 require 项目根 node\_modules/sqlite3，better-sqlite3 不可用）。

* 备份：backup-db.js + Windows 计划任务 FundSimulator-DB-Backup（每日 21:00，保留 30 份）；恢复 = 停服 → 备份文件覆盖 fund\_simulator.db → 重启。



***

## 六、工程约定（长期）



1. **改后端一律 Python 脚本**（io.open 读改写）+ `node --check`；**禁止 PowerShell 内联 node -e 改代码**（引号会坏）。

2. Python 匹配后端代码用**索引切片**代替精确字符串（空行缩进会导致 count==0）；断言失败时内存改动不落盘，需幂等完整脚本重跑。

3. 改后端 → 部署中心 restart → API / 日志验证；改前端 → frontend/ 下 npm run build → 浏览器？t= 强刷验收。

4. 涉及时间 / 日期的改动必须检查 UTC / 本地时区（见 §3.1）。

5. 验收走 browser-use-automation（computer\_use\_tool plane=bu）：页面文本 /console/ 截图，AntD 元素用原生 click。

6. 外部数据源（天天基金 / 东财 / 新浪）接口可能反爬 / 下线（fundgz 已死），一律准备回退链。

7. 规则性结论同步写入 `.workbuddy\memory\2026-09-18.md`（或当日文件）与本文档，保证后续轮次可查。



***

## 七、缺陷修复史（规则沉淀来源）



| 日期    | 缺陷                                   | 修复规则                                                                                 |
| ----- | ------------------------------------ | ------------------------------------------------------------------------------------ |
| 09-17 | server.js 每次启动 DROP TABLE 清库（交易记录丢失） | initDatabase 改幂等；已加每日备份                                                              |
| 09-17 | 交易时间显示差 8 小时（UTC 当本地）                | 前端 normalizeDateStr 按 UTC 转本地                                                        |
| 09-17 | 当日买入被算当日收益                           | T+1 感知：今日买入今日盈亏 = 0、涨跌显示 "—"、T+1 标签                                                  |
| 09-17 | 观察池假数据（Math.random）+ 名单写死            | 改真实自选 + 真实信号引擎                                                                       |
| 09-17 | "点立即分析就买入"                           | /api/ai/analyze 只出建议不成交；后续 performAnalysis 加 auto 隔离                                 |
| 09-17 | 观察池没有 "观察的样子"                        | 信号徽章 + 指标 + 理由（buy/add/watch/wait）                                                   |
| 09-17 | 用户切换后菜单高亮不对                          | activeIndex 改 computed (route.path)                                                  |
| 09-17 | 全站浅色重构 "差别不大"                        | 深色金融科技风 + 柔和化（#131a35）                                                               |
| 09-17 | el-table 斑马纹深色刺眼                     | 覆盖 --el-fill-color-lighter 半透明                                                       |
| 09-17 | 分页组件深色不适配                            | 分页规则！important 深色                                                                    |
| 09-18 | 赎回费持有天数错（永远 1 天）                     | 从首次买入日算持有天数                                                                          |
| 09-18 | 手续费口径不真实                             | fund\_fees 真实费率 + 内扣法 + FIFO 分批赎回                                                    |
| 09-18 | 卖出赎回费未入账（现金虚高）                       | realized\_pnl 账本                                                                     |
| 09-18 | 净值同步缺失（最新只到 9-16）                    | 每日 21:30 自动同步 + 启动补拉                                                                 |
| 09-18 | 订单确认用下单快照净值                          | 确认取 T 日官方净值                                                                          |
| 09-18 | 详情弹窗节点增长率 "—"                        | 日期斜杠 / 横线归一化                                                                         |
| 09-18 | 详情页经理 / 成立日期 / 基准 "—"                | f10 抓真实资料 UPDATE（4 只）                                                                |
| 09-18 | 区间涨跌幅算不出                             | 全量历史净值补齐（成立日起）                                                                       |
| 09-18 | 两性格观察池重叠（000001 等 5 只）               | 性格专属类型池（零交集）+ 跨用户去重防御                                                                |
| 09-18 | AI 只看 17 只                           | 全市场 fund\_universe 14,359 + 全市场性格选基                                                  |
| 09-18 | 基金库被 AI 选基喂大                         | 基金库 = 全市场（universe），与观察池独立                                                           |
| 09-18 | 观察池 8 只硬上限不流动                        | 不设上限 + 09:35/17:00 周期扫描 + MAX\_POOL=25 防御                                            |
| 09-18 | 只在 15:00 下单、20:00 才确认                | 盘中 30 分钟 /pre\_close/close 三周期下单 + trade\_date 归属                                    |
| 09-18 | "凌晨 02:25 交易"（时区显示 bug）              | Alerts/Reports 转本地 + 报告正文 utcToLocalStr                                              |
| 09-18 | 盘外可下单                                | order-engine 交易时段硬校验（工作日 09:00-15:05）                                                |
| 09-18 | 已持有不再加仓（违背分批建仓）                      | 冷却期（5/3 天）后按 10% 分批加仓 + 单基金上限兜底                                                      |
| 09-18 | 节假日照常可交易（周末已排除但法定假日未内置）              | engine/holidays.json 2026 休市表 + isTradingDay 硬校验 + 调度顺延下一交易日（verify-calendar 33 例通过） |
| 09-18 | funds 表被 AI 扫描喂大（101 只，大量淘汰孤儿） | 清理 42 只无引用基金（funds→59），净值历史保留；基金库=universe 不受影响；定期重跑 cleanup-funds-orphans.js |
| 09-18 | 归因结果不写入月报正文（仅 API 返回） | generateReport 月报追加"业绩归因（简化 Brinson）"小节（配置/选基/总超额） |
| 09-18 | 累计收益恒 0（总资产=现金+持仓成本，非市值） | /api/ai/portfolio 补 latest_nav/market_value/today_pnl，total_assets 改市值口径；Home.vue 卡片改用后端市值与快照盈亏 |
| 09-18 | 详情弹窗基金经理/成立日期/基准显示 "—"（funds 表数据完好） | 根因：Home.vue 从 /api/funds 列表（fund_universe，无 manager/benchmark）取数；改取 /api/funds/:code（funds 表 SELECT *）；基金详情页本就正确 |



***

## 八、当前状态与验收基准（2026-09-18 晚）



* 观察池：default 28 只（25 AI + 3 手动）、aggressive 20 只（17 AI + 3 手动），两池零交集，全部带信号。

* 持仓：default 005827（6,695.88 份，成本 9,983.78）+ 000001（6,163.60 份，成本 8,000）；aggressive 161725（37,847.15 份）+ 005267（7,097.35 份）。

* 现金：default 81,851.22 /aggressive 64,001.82（费后口径）。

* 订单：orders 表 14 列含 trade\_date；9 条记录；SUBMITTED 待确认 2 条（aggressive 161725 SELL 18,943 份、000001 BUY ¥6,400，trade\_date=09-18，次日 20:00 确认）。

* 已实现盈亏：default -165.00（005827 卖出）。

* 净值：跟踪基金全量历史齐（005827 1,928 条 / 161725 2,756 条 / 000001 6,000 条 / 005267 2,129 条）；最新 2026-09-18 净值 21:30 同步。

* 基金库：GET /api/funds total=14,359；搜索 "白酒"→2 只；类型 "指数型"→4,507 只。

* 调度：全部周期已排程（09:35 / 盘中 30 分钟 / 14:30/15:00/20:00/21:30/22:05）；手动触发只出决策不下单（实测订单数不变）。



***

## 九、遗留事项（未决 / 待办）



1. ~~法定节假日交易日历未内置~~ **已完成（2026-09-18）**：engine/holidays.json 2026 休市表 + isTradingDay 硬校验 + 收盘前 / 收盘 / 盘中调度顺延下一交易日；verify-calendar.js 33 例边界全过；每年 11 月国务院公布次年安排后补充 JSON 即可。

2. ~~funds 表历史 AI 新入的基金未清理~~ **已完成（2026-09-18）**：清理 42 只无引用孤儿（funds 101→59；不在 watchlist/holdings/orders/transactions/fund_fees 的行），真实净值历史保留（62509 条，重新入库可复用）；清理脚本 `fund-simulator\cleanup-funds-orphans.js`；基金库页面不受影响（查 universe）。注：AI 扫描仍会持续入库新基金，观察池淘汰后 funds 行会再积累，定期重跑该脚本即可。

3. ~~定投 / 定期计划（规格 §4.3）~~ **评估结论（2026-09-18）：不实施**——设计文档本就标"⬜ 可选"；AI 的定期小额加仓语义已由"分批加仓 + 冷却期（5/3 天）"覆盖，且系统铁律是 AI 自主决策（用户设定的机械定投与此冲突），另开一条买入路径反而增加"乱买"风险。

4. ~~分红 / 归因 / 压力测试月度触发待验证~~ **已完成（2026-09-18）**：链路本就实现（分红每月 1-3 日自动同步、归因/压力/月报月末最后交易日自动触发），手动 POST /api/scheduler/run type=monthly 实测全通（default 归因 配置 0.40%/选基 -1.19%/总超额 -0.80%；aggressive 0.45%/-1.27%/-0.82%，压力报告+月报落库）；**修复缺口：归因结果此前只回 API 不写月报正文，现月报追加"业绩归因（简化 Brinson）"小节**。

5. ~~未跟踪基金 ☆ 观察待验收~~ **已完成（2026-09-18，浏览器实测通过）**：基金库 012414 ☆ 观察 → POST 自动入库（universe 兜底）+ 拉全量净值（1300 条）→ ★ 已观察 → 详情页完整渲染 → AI 信号"暂缓入场"（近20日 -5%、20日线下方），全程只读不交易；验收数据已回滚（watchlist 恢复 56、funds 删除、净值保留）。备注：bu.click 对 AntD 按钮偶发不触发，需 JS dispatch click。

6. ~~fund\_universe 每日 22:05 自动刷新待验证~~ **已完成（2026-09-18）**：启动日志确认排程生效（"每日 22:05 自动刷新，首次 2026/9/18 22:05"）；首次自动执行发生在今晚 22:05，次日查日志（[全市场基金库] 开始刷新…code=0）即可确认。

7. ~~项目尚无 Git 仓库~~ **已完成（2026-09-18）**：根目录 `git init` 首次提交 228a808（242 文件，含运行数据库、知识库、设计规格、engine 修复脚本、README 新环境运行指引、.gitignore 排除 node_modules/dist/bak）。**维护铁律：规则/缺陷/功能改动必须同步文档（本文档 + .workbuddy/memory）并随代码一起 commit**。