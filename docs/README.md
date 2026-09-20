# fund-simulator・AI 基金模拟操盘系统

本地部署的 AI 自主操盘基金模拟交易系统（用户只读查看，AI 按用户性格自主扫描、观察、交易）。

前端 Ant Design Vue + Vite，后端 Node.js（Express），数据 SQLite。

## 目录



```
fund/

├── fund-simulator/            # 应用主体

│   ├── server.js              # 后端主服务（端口 3000）

│   ├── frontend/              # 前端（AntD Vue 3 + Vite）

│   ├── engine/                # 数据修复/治理脚本（Python/Node）

│   ├── fund\_simulator.db      # 运行数据库（账目/持仓/交易/净值/观察池）

│   └── api/ public/ data/     # 路由 / 静态资源 / 数据

├── SYSTEM\_KNOWLEDGE.md        # 系统知识库（口径、规则、修复史）★ 每次维护必同步

├── AI\_FUND\_OPERATIONS\_DESIGN.md  # 系统设计规格

└── .workbuddy/memory/         # 每日规则沉淀
```

## 新环境运行步骤



1. 安装 Node.js 22（推荐 22.22.x），确保 `node`、`npm` 在 PATH。

2. 安装依赖：



```
cd fund-simulator

npm install

cd frontend

npm install
```



1. 构建前端（可选，开发态也可用 Vite 热更新）：



```
cd fund-simulator/frontend

npm run build
```



1. 启动后端（端口 3000）：



```
cd fund-simulator

node server.js
```



1. 浏览器访问 `http://localhost:3000/`（内嵌部署中心 127.0.0.1:8900 托管时，重启走

   `POST http://127.0.0.1:8900/api/services/fund-simulator/restart`，日志在部署中心 logs 下）。

数据库 `fund_simulator/fund_simulator.db` 已入库，包含当前账目、持仓、交易、净值与观察池，

拉取仓库后即可接着运行；如需清空重建可参考 `seed-data.js`。

## 核心口径（速查，详见 SYSTEM\_KNOWLEDGE.md）



* 整个系统只能查看：无手动交易入口，AI 自主操盘（按用户性格扫描全市场 → 观察池 → 信号 → 盘中下单）。

* 交易时点：盘中三周期（realtime /pre\_close/close）才下单；20:00 T+1 确认；21:30 / 22:30 净值同步。

* 手续费：买入记申购费、卖出记赎回费，费率按真实基金规则（<7 天 1.5% 等），内扣法，Σ transactions.fees 对账。

* 收益口径：账户累计 = 已实现（realized\_pnl 账本）+ 浮动（市值−成本）；单基金每日盈亏 = 收盘份额 ×（当日净值−前日净值），买入当日 T+1 无收益。

* 快照守卫：全部持仓基金当日净值公布后才写当日快照，否则今日盈亏显示 "待更新"。

## 维护约定



* 任何规则 / 口径调整、缺陷修复，必须同步写入 `SYSTEM_KNOWLEDGE.md` 与 `.workbuddy/memory/`，并随代码一起提交 git。

* 修复脚本放 `fund-simulator/engine/`，命名 fix-*.py / fix-*.js，可复跑。