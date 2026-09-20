# 基金模拟交易系统需求文档

## 1. 项目概述

### 1.1 项目目标
开发一个基于真实基金净值数据的模拟交易系统，让用户能够在不使用真实资金的情况下，体验基金投资的全过程，包括基金选择、买入卖出、持仓管理、收益分析等。

### 1.2 核心原则
- **真实数据**：所有基金净值、行情数据必须来自真实数据源，禁止使用模拟或随机生成的数据
- **虚拟资金**：交易资金为虚拟货币，不涉及真实资金流动
- **完整体验**：提供完整的基金投资体验，从开户到交易到分析

## 2. 团队分工

### 2.1 交易分销团队（金融业务团队）
**职责范围**：
1. **基金产品知识库**
   - 基金分类体系（股票型、混合型、债券型、货币型等）
   - 基金评价指标（夏普比率、最大回撤、阿尔法、贝塔等）
   - 基金费率结构（管理费、托管费、申购费、赎回费等）

2. **交易规则设计**
   - 交易时间规则（T日15:00前申购，T+1日确认）
   - 最低申购金额/份额限制
   - 定投规则设计
   - 分红方式选择（现金分红/红利再投资）

3. **风险指标计算模型**
   - 收益率计算（累计收益率、年化收益率、基准对比）
   - 风险指标计算（波动率、最大回撤、夏普比率）
   - 绩效归因分析

4. **业务需求定义**
   - 用户角色定义
   - 业务流程设计
   - 验收标准制定

### 2.2 软件开发团队（技术团队）
**职责范围**：
1. **系统架构设计**
   - 技术选型（前端Vue+Vite，后端Node.js）
   - 数据库设计（SQLite）
   - API接口设计

2. **前端开发**
   - 用户界面设计与实现
   - 交互逻辑开发
   - 数据可视化（图表展示）

3. **后端开发**
   - RESTful API开发
   - 数据采集服务
   - 业务逻辑实现

4. **数据层开发**
   - 真实数据源对接
   - 数据清洗与存储
   - 数据更新机制

5. **测试与部署**
   - 单元测试
   - 集成测试
   - 部署上线

## 3. 功能需求

### 3.1 用户管理模块
- 用户注册/登录（可选，可先使用默认用户）
- 个人资料管理
- 投资偏好设置

### 3.2 基金数据模块
- **基金信息展示**
  - 基金列表（按类型、业绩、规模等筛选）
  - 基金详情页（基本信息、历史净值、基金经理、持仓明细）
  - 基金比较功能

- **数据更新**
  - 每日自动更新基金净值
  - 实时估值展示（交易时间内）
  - 数据异常处理

### 3.3 交易模块
- **模拟交易**
  - 买入基金（指定金额或份额）
  - 卖出基金（指定份额）
  - 定投设置（定期定额投资）

- **交易记录**
  - 交易历史查询
  - 交易详情查看
  - 交易导出功能

### 3.4 投资组合模块
- **持仓管理**
  - 当前持仓展示
  - 持仓成本计算
  - 持仓盈亏分析

- **资产配置**
  - 资产分布饼图
  - 行业配置分析
  - 风险敞口分析

### 3.5 分析报告模块
- **收益分析**
  - 累计收益曲线
  - 收益分布统计
  - 基准对比分析

- **风险分析**
  - 风险指标计算
  - 风险收益散点图
  - 最大回撤分析

- **绩效报告**
  - 月度/季度/年度报告
  - 绩效归因分析
  - 投资建议生成

### 3.6 AI智能分析模块
- **交易分析团队集成**
  - 集成交易分析团队（12位专业分析师）
  - 支持对基金进行系统性投资分析
  - 提供多维度综合分析报告

- **分析流程**
  - Phase 1: 数据收集（技术分析、基本面分析、新闻分析、情绪分析）
  - Phase 2: 多空辩论（多头论证、空头论证、研究主管裁决）
  - Phase 3: 交易决策（入场价、目标价、止损价、仓位建议）
  - Phase 4: 风险评估（激进、保守、中性三方风险辩论）
  - Phase 5: 最终报告（结构化投资分析报告）

- **AI分析报告**
  - 综合评分雷达图（技术面/基本面/新闻面/情绪面/风险面）
  - 多空论点对比图
  - 风险评估三角图
  - 详细分析文本区
  - 最终交易决策（BUY/SELL/HOLD）

- **智能建议**
  - 基于分析结果的交易建议
  - 风险提示和注意事项
  - 投资策略推荐

### 3.6 系统设置模块
- 交易费率设置
- 数据源配置
- 系统参数调整

## 4. 非功能需求

### 4.1 性能需求
- 页面加载时间 < 3秒
- API响应时间 < 500ms
- 支持100+并发用户

### 4.2 数据需求
- 数据准确性：净值数据误差 < 0.01%
- 数据完整性：历史数据至少3年
- 数据时效性：交易日数据当日更新

### 4.3 安全需求
- 用户数据加密存储
- API接口鉴权
- 防SQL注入、XSS攻击

### 4.4 可用性需求
- 界面友好，操作简单
- 响应式设计，支持移动端
- 提供操作指引和帮助文档

## 5. 技术架构

### 5.1 前端技术栈
- **框架**：Vue 3
- **构建工具**：Vite
- **状态管理**：Pinia
- **UI组件库**：Element Plus
- **图表库**：ECharts
- **HTTP客户端**：Axios

### 5.2 后端技术栈
- **运行时**：Node.js
- **框架**：Express.js
- **数据库**：SQLite
- **数据采集**：Axios + Cheerio
- **定时任务**：node-cron

### 5.3 数据源
- **主要数据源**：天天基金网API
- **备用数据源**：好买基金、东方财富
- **数据格式**：JSON

### 5.4 部署架构
- **开发环境**：本地开发
- **测试环境**：Docker容器
- **生产环境**：云服务器

## 6. 数据库设计

### 6.1 核心表结构
```sql
-- 基金信息表
CREATE TABLE funds (
    fund_code TEXT PRIMARY KEY,
    fund_name TEXT NOT NULL,
    fund_type TEXT,
    inception_date TEXT,
    manager TEXT,
    benchmark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 基金净值表
CREATE TABLE fund_nav (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code TEXT NOT NULL,
    nav_date TEXT NOT NULL,
    unit_nav REAL,
    acc_nav REAL,
    daily_return REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fund_code) REFERENCES funds (fund_code),
    UNIQUE(fund_code, nav_date)
);

-- 用户投资组合表
CREATE TABLE portfolios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT DEFAULT 'default_user',
    portfolio_name TEXT NOT NULL,
    initial_capital REAL DEFAULT 100000,
    current_capital REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 持仓明细表
CREATE TABLE holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER NOT NULL,
    fund_code TEXT NOT NULL,
    shares REAL DEFAULT 0,
    cost_price REAL,
    current_price REAL,
    market_value REAL,
    profit_loss REAL,
    profit_loss_rate REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id),
    FOREIGN KEY (fund_code) REFERENCES funds (fund_code)
);

-- 交易记录表
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER NOT NULL,
    fund_code TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    amount REAL NOT NULL,
    price REAL NOT NULL,
    shares REAL NOT NULL,
    fees REAL DEFAULT 0,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id),
    FOREIGN KEY (fund_code) REFERENCES funds (fund_code)
);
```

## 7. API接口设计

### 7.1 基金相关接口
- `GET /api/funds` - 获取基金列表
- `GET /api/funds/:code` - 获取基金详情
- `GET /api/funds/:code/nav` - 获取基金净值历史
- `GET /api/funds/:code/estimate` - 获取基金实时估值

### 7.2 交易相关接口
- `POST /api/portfolios/:id/buy` - 买入基金
- `POST /api/portfolios/:id/sell` - 卖出基金
- `GET /api/portfolios/:id/transactions` - 获取交易记录

### 7.3 组合相关接口
- `GET /api/portfolios` - 获取投资组合列表
- `POST /api/portfolios` - 创建投资组合
- `GET /api/portfolios/:id/holdings` - 获取持仓信息
- `GET /api/portfolios/:id/performance` - 获取组合表现

### 7.4 分析相关接口
- `GET /api/portfolios/:id/analysis` - 获取分析报告
- `GET /api/portfolios/:id/risk` - 获取风险指标

## 8. 开发计划

### 8.1 第一阶段：需求分析与设计（1周）
- 交易分销团队：完成业务需求文档
- 软件开发团队：完成技术方案设计

### 8.2 第二阶段：数据层开发（1周）
- 软件开发团队：实现数据采集服务
- 交易分销团队：验证数据准确性

### 8.3 第三阶段：核心功能开发（2周）
- 软件开发团队：实现交易引擎、组合管理
- 交易分销团队：验证业务逻辑

### 8.4 第四阶段：前端开发（2周）
- 软件开发团队：实现用户界面
- 交易分销团队：用户体验测试

### 8.5 第五阶段：集成测试与部署（1周）
- 共同进行系统测试
- 部署上线

## 9. 验收标准

### 9.1 功能验收
- 所有功能按需求文档实现
- 业务流程完整无遗漏
- 异常处理完善

### 9.2 数据验收
- 真实数据源对接成功
- 数据更新机制正常
- 数据准确性达标

### 9.3 性能验收
- 页面加载时间达标
- API响应时间达标
- 并发处理能力达标

### 9.4 用户体验验收
- 界面设计符合用户习惯
- 操作流程简单直观
- 错误提示清晰明确

## 10. 风险与应对

### 10.1 数据源风险
- **风险**：数据源接口变更或不可用
- **应对**：多数据源备份，异常监控告警

### 10.2 技术风险
- **风险**：技术难点无法攻克
- **应对**：技术预研，及时调整方案

### 10.3 进度风险
- **风险**：开发进度滞后
- **应对**：每日站会，及时调整资源

### 10.4 质量风险
- **风险**：系统存在严重缺陷
- **应对**：代码审查，自动化测试

## 11. 沟通机制

### 11.1 日常沟通
- 每日站会（15分钟）
- 即时通讯（企业微信/钉钉）
- 代码审查（GitLab/GitHub）

### 11.2 阶段评审
- 周例会（进度同步）
- 里程碑评审（阶段验收）
- 复盘会议（经验总结）

### 11.3 文档管理
- 需求文档（Confluence/语雀）
- 设计文档（Markdown）
- 接口文档（Swagger/OpenAPI）