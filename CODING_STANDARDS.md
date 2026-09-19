# 代码规范（CODING STANDARDS）

> 本规范适用于 fund-simulator 全仓。所有新增/重构代码必须遵守；老代码在重构中逐步对齐。

## 一、总则

1. **功能优先，重构不破坏现有行为**：每次改动必须可运行、可验证，不允许"重构中跑不起来"。
2. **小步提交**：一个职责一次 commit，commit message 用 `type: 描述`（feat/fix/refactor/style/chore）。
3. **不过度设计**：三个相似片段再抽象；两个就复制。抽象成本高于复制成本时不抽象。

## 二、后端（Node.js + Express + SQLite）

### 2.1 目录结构（模块颗粒化）

```
server.js              # 仅做装配：require 各模块 + listen，不写业务逻辑
config/
  db.js                # SQLite 单例连接（唯一出处）
  constants.js         # HOLIDAYS、交易时段、费率默认值等常量
events/
  aiBus.js             # EventEmitter 单例（AI 事件总线）
middleware/
  errorHandler.js      # 统一错误处理（4 参数 Express 中间件）
  asyncHandler.js      # async 路由包装器（try/catch 收拢）
  tradingGuard.js      # 交易时段/交易日守卫（isMarketOpenNow/isTradingDay）
services/              # 业务逻辑层（无 HTTP 细节，纯数据操作）
  portfolio.service.js
  analysis.service.js  # performAnalysis 主流程
  report.service.js    # generateReport 各类型
  watchlist.service.js # aiDiscoverWatchlist
  fee.service.js
  market.service.js
engine/                # 决策引擎（纯函数/策略）
  signal.js            # getFundSignal
  risk.js              # checkRiskControls / logRiskEvent
  order.js             # orderEngine 封装
  strategy/            # 设计模式：策略——按用户性格分叉
    base.strategy.js
    stable.strategy.js
    aggressive.strategy.js
routes/                # 路由层（仅参数解析+调 service）
  ai.routes.js
  funds.routes.js
  reports.routes.js
  scheduler.routes.js
  market.routes.js
```

### 2.2 设计模式使用

| 场景 | 模式 | 实现 |
|---|---|---|
| DB 连接 | 单例 | `config/db.js` 导出唯一 db 实例 |
| AI 事件流 | 观察者 | `events/aiBus.js`（已有） |
| 报告生成 | 工厂 | `report.service.js` 按 type 分发 daily/weekly/monthly/pressure |
| 用户性格决策 | 策略 | `engine/strategy/*.js`——stable/aggressive 实现同一接口（止损线/建仓比例/入场阈值） |
| 异步路由错误 | 装饰器 | `asyncHandler(fn)` 收拢 try/catch |
| 日志 | 门面 | `logAi()` 统一入口：console + SSE + ai_event_logs |

### 2.3 统一出口（收拢原则）

- **SQLite**：所有 `new sqlite3.Database` 只在 `config/db.js`，其他文件 `require('../config/db')`。
- **HTTP 响应**：成功 `res.json({ok:true, data})`，失败走 `errorHandler`，不允许各路由自己 try/catch 拼错误。
- **时间**：`getLocalDateStr()` 唯一时间格式函数，不允许各处手拼。
- **费率计算**：`fee.service.js` 唯一，不允许路由里手算 fees。
- **AI 日志**：所有 AI 关键节点必须 `logAi(type, payload)`，不允许 `console.log` 裸奔（调试日志除外）。

### 2.4 注释规则

- 函数上方一句话 JSDoc：`// 拉取用户持仓 + 最新净值 + 市值（T+1 待确认按成本计）`
- 复杂业务规则必须注释"为什么"：`// 周末/节假日不跑 close：无新净值，避免空日报`
- 不注释"是什么"（代码自解释），不注释显而易见的事
- 禁掉临时 `// TODO: xxx` 超过 3 天——要么做要么删

## 三、前端（Vue3 + Ant Design Vue + ECharts）

### 3.1 目录结构

```
src/
  api/                 # 统一 API 出口（所有 axios 调用只在这里）
    client.js           # axios 实例 + 拦截器（统一错误提示）
    ai.api.js
    funds.api.js
    reports.api.js
    market.api.js
  components/           # 可复用组件（无业务耦合）
    StatCard.vue        # 数字卡（标题+数值+涨跌色）
    FundTable.vue       # 基金表格（排行/对比共用）
    ChartCard.vue       # ECharts 容器（自动 resize）
    EmptyState.vue      # 空状态
    TagPill.vue         # 徽章
  composables/          # 组合式函数
    useSSE.js           # EventSource 封装
    useUser.js          # 当前用户切换
  stores/               # 轻量状态（Pinia 或 reactive 单例）
    user.store.js
  views/                # 页面（薄，只组合组件）
  router/
```

### 3.2 组件复用规则

- 两个页面以上用到的 UI 块必须抽到 `components/`
- 基金表格、数字卡、图表卡是系统三大重复块，必须组件化
- 页面文件不超过 300 行——超过就拆子组件
- ECharts 初始化必须包在 `ChartCard.vue`，父组件只传 option

### 3.3 交互规范

- **红涨绿跌**（A 股习惯）：涨 #f87171 系，跌 #34d399 系，全局 CSS 变量 `--up/--down`
- 数字格式统一：`¥xxx,xxx.xx`、`+x.xx%`，封装 `formatMoney/formatPct`
- 时间用相对格式：`3 分钟前 / 昨天 15:00`
- 加载态：所有数据区有骨架屏或"加载中"，不允许白屏
- 空状态：EmptyState 组件，带引导文案

## 四、Git 与提交

- 每次功能完整且可运行才 commit
- commit 前缀：`feat:` 新功能 / `fix:` 修复 / `refactor:` 重构不改行为 / `style:` 样式 / `docs:` 文档
- push 前 `node --check`（后端）+ `npm run build`（前端）必须通过

## 五、测试要求

- 后端改动：node --check + 启动后 curl 对应 API 验证返回
- 前端改动：npm run build 通过 + 浏览器强刷验证页面无报错
- 数据库改动：写迁移脚本，不手改线上库
- 每批完成后更新 SYSTEM_KNOWLEDGE.md + .workbuddy/memory

## 六、AI 自身遵循的规则（补充）

- **不编造数据**：外部接口失败就说失败，不模拟成功
- **不静默降级**：功能做不成就明说缺什么，不假装完成
- **交易安全**：所有下单路径必经 checkRiskControls + 交易时段守卫，重构不允许绕过
- **留档**：AI 所有决策（信号/下单/风控/选基）必须落库，实时推送同时写库
