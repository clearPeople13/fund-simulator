# 代码规范（CODING STANDARDS）

> 本规范适用于 fund-simulator 全仓。所有新增/重构代码必须遵守；老代码在重构中逐步对齐。

## 一、总则

1. **功能优先，重构不破坏现有行为**：每次改动必须可运行、可验证，不允许"重构中跑不起来"。
2. **小步提交**：一个职责一次 commit，commit message 用 `type: 描述`（feat/fix/refactor/style/chore）。
3. **不过度设计**：三个相似片段再抽象；两个就复制。抽象成本高于复制成本时不抽象。
4. **思考先行，不盲目编码**：收到需求后先想清楚——
   - 这个问题的根因是什么？（不是表面症状）
   - 真实业务规则是什么？（如：基金净值 21:30 才公布，不是 15:00）
   - 改了这个地方，其他地方会不会受影响？
   - 有没有更优解？（不是第一个想到的方案就直接写）
   - **想清楚了再动手**，不要"先改了再说，用户不满意再改"。
5. **用户描述不准确时主动更正**：用户说的不一定全对——
   - 如果用户的描述和真实业务规则矛盾（如"15点复盘" vs "净值21:30才公布"），**主动指出并给出正确方案**，不要盲从。
   - 举例：用户说"15点收盘后复盘"，但基金净值 21:30 才公布，应该说"15点复盘时净值还没出来，建议 21:30 净值公布后复盘"。
   - 不要因为是用户说的就照做——用户要的是正确结果，不是机械执行。
6. **5 个审核 agent 视角**：每个改动做完后，必须过这 5 个 agent 的审核，没问题才交付——
   - **基金经理 agent**（核心业务）：从真实基金交易视角审查——系统缺什么功能？和支付宝/天天基金比差什么？交易规则对不对？（如：申购费/赎回费/持有期费率/T+1确认/净值公布时间）
   - **功能 agent**：业务逻辑对不对？边界条件？异常处理？
   - **代码 agent**：代码规范/设计模式/复用性/注释/命名
   - **UI agent**：视觉/间距/颜色/响应式/字体/对齐
   - **交互 agent**：操作流程/用户体验/是否符合基金 App 习惯/有没有反直觉的设计
7. **文档自动更新链条**（不靠用户提醒，触发就更新）：
   - **改了业务规则**（如：每日复盘时间从 15:00 改成 21:30）→ 同步更新 SYSTEM_KNOWLEDGE.md + CODING_STANDARDS.md
   - **加了新功能**（如：费用统计/压力测试）→ 同步更新 README.md 功能列表 + SYSTEM_KNOWLEDGE.md
   - **修了 bug**（如：000001 基金名称错误）→ 同步更新 SYSTEM_KNOWLEDGE.md "缺陷修复史"
   - **改了 UI/交互**（如：header 布局/卡片间距）→ 同步更新 README.md "界面说明"
   - **改了目录结构**（如：前后端分离）→ 同步更新 README.md "目录结构"
   - **每次 commit 前**：检查文档是否需要同步更新，需要就一起 commit
   - **例外**：用户手动改的文档（如用户自己写的需求）不需要自动更新

## 二、后端（Node.js + Express + SQLite）

### 2.1 目录结构（实际）

```
backend/
├── server.js          # 入口：装配 + listen（业务逻辑已抽离）
├── data-fetcher.js    # 基金数据抓取
├── package.json
├── fund_simulator.db  # SQLite 数据库
├── api/               # 旧 API 路由
├── routes/            # Express 路由层（按职责分文件）
│   ├── users.js       # 用户路由 8 个
│   ├── readonly.js    # 只读查询 19 个
│   ├── system.js      # 系统/SSE/调度 5 个
│   └── ai.js          # AI 核心 6 个
├── services/         # 业务逻辑层（无 HTTP 细节）
│   ├── hotspots.js    # 热点分析引擎
│   └── portfolio.js   # 组合服务（getUserPortfolio/saveTransaction/updateHolding/getAnalysisResults）
├── engine/            # 决策引擎（order-engine/fee/holidays）
├── events/
│   └── aiBus.js       # EventEmitter 单例（AI 事件总线）
├── middleware/
│   └── errorHandler.js # 统一错误处理
├── utils/
│   └── time.js        # 时间/交易日纯函数
├── scripts/           # 一次性脚本
└── data/              # 数据文件
```

### 2.2 设计模式使用

| 场景 | 模式 | 实现 |
|---|---|---|
| DB 连接 | 单例 | `server.js` 里 `new sqlite3.Database` |
| AI 事件流 | 观察者 | `events/aiBus.js` |
| 路由分组 | 工厂 | `routes/*.js` 导出 `(ctx) => Router` |
| 异步路由错误 | 中间件 | `middleware/errorHandler.js` |
| 日志 | 门面 | `logAi()` 统一入口 |

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

### 3.1 目录结构（实际）

```
frontend/src/
├── api/
│   └── client.js       # axios 实例 + fmtMoney/fmtPct/fmtTime
├── components/        # 可复用组件
│   ├── StatCard.vue    # 数字卡
│   └── EmptyState.vue  # 空状态
├── composables/
│   └── useSSE.ts       # SSE 封装
├── router/
│   └── index.ts
├── types/              # TypeScript 类型定义
├── views/              # 页面
│   ├── Home.vue
│   ├── Funds.vue
│   ├── FundDetail.vue
│   ├── Portfolio.vue
│   ├── Analysis.vue
│   ├── Market.vue
│   ├── Alerts.vue
│   ├── Reports.vue
│   └── Profile.vue
├── App.vue
├── main.ts
└── style.css           # 红涨绿跌全局变量
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
