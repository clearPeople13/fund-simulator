# 基金模拟交易系统

基于真实基金净值数据的模拟交易平台，支持完整的基金投资体验。

## 系统架构

```
├── 前端 (Vue 3 + Vite)
│   ├── 首页仪表盘
│   ├── 基金列表与详情
│   ├── 投资组合管理
│   ├── 模拟交易
│   ├── 投资分析
│   └── AI智能分析 (集成交易分析团队)
│
├── 后端 (Node.js + Express)
│   ├── RESTful API
│   ├── 数据采集服务 (天天基金)
│   └── SQLite 数据库
│
└── 数据源
    └── 天天基金网 (真实基金净值数据)
```

## 核心功能

1. **基金数据管理** - 真实基金净值数据采集与展示
2. **模拟交易** - 使用虚拟资金进行买卖操作
3. **投资组合** - 持仓管理与资产配置分析
4. **收益分析** - 收益曲线、风险指标、绩效归因
5. **AI智能分析** - 集成交易分析团队12位专业分析师

## 技术栈

### 前端
- Vue 3 + Vite
- Element Plus (UI组件库)
- ECharts (数据可视化)
- Vue Router (路由管理)
- Pinia (状态管理)
- Axios (HTTP客户端)

### 后端
- Node.js + Express
- SQLite3 (数据库)
- Axios + Cheerio (数据采集)

## 快速开始

### 1. 安装依赖

```bash
# 后端依赖
cd fund-simulator
npm install

# 前端依赖
cd frontend
npm install
```

### 2. 启动系统

**Windows:**
```bash
# 双击运行 start.bat
# 或手动启动:
# 终端1: node server.js
# 终端2: cd frontend && npm run dev
```

**Linux/Mac:**
```bash
# 终端1: node server.js
# 终端2: cd frontend && npm run dev
```

### 3. 访问系统

- 前端: http://localhost:5173
- 后端API: http://localhost:3000

## 项目结构

```
fund-simulator/
├── server.js              # 后端服务器
├── server-production.js   # 生产环境服务器
├── data-fetcher.js        # 数据采集模块
├── api/
│   └── routes.js          # API路由
├── frontend/
│   ├── src/
│   │   ├── App.vue        # 主应用组件
│   │   ├── main.js        # 入口文件
│   │   ├── router/
│   │   │   └── index.js   # 路由配置
│   │   └── views/
│   │       ├── Home.vue   # 首页
│   │       ├── Funds.vue  # 基金列表
│   │       ├── FundDetail.vue  # 基金详情
│   │       ├── Portfolio.vue   # 投资组合
│   │       ├── Trading.vue     # 交易页面
│   │       ├── Analysis.vue    # 分析页面
│   │       ├── AIAnalysis.vue  # AI分析页面
│   │       └── NotFound.vue    # 404页面
│   ├── package.json
│   └── vite.config.js
├── start.bat              # Windows启动脚本
├── REQUIREMENTS.md        # 需求文档
└── PROJECT_PLAN.md        # 项目计划
```

## 团队分工

### 交易分销团队 (金融业务)
- 基金产品知识库
- 交易规则设计
- 风险指标计算
- 业务需求定义

### 软件开发团队 (技术)
- 系统架构设计
- 前后端开发
- 数据接口对接
- 测试与部署

## 数据源说明

系统使用天天基金网作为主要数据源，获取真实的基金净值数据。数据包括：
- 基金基本信息（代码、名称、类型、经理等）
- 历史净值数据
- 实时估值数据

## AI智能分析

系统集成了"交易分析团队"，包含12位专业分析师：

1. 技术分析师 - 价格走势与技术指标
2. 基本面分析师 - 财报解读与估值分析
3. 新闻分析师 - 公司公告与行业政策
4. 情绪分析师 - 资金流向与机构评级
5. 多头研究员 - 买入论证
6. 空头研究员 - 卖出论证
7. 研究主管 - 裁决多空辩论
8. 交易员 - 交易决策
9. 激进风险分析师 - 上行空间分析
10. 保守风险分析师 - 下行风险分析
11. 中性风险分析师 - 平衡视角
12. 风险主管 - 最终风险评估

## 注意事项

1. 本系统仅供学习交流，不构成任何投资建议
2. 交易资金为虚拟货币，不涉及真实资金流动
3. 数据来源于公开市场信息，仅供参考
4. 投资有风险，决策需谨慎