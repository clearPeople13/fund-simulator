# AI自动操盘系统 - TypeScript 开发指南

## 技术栈

- **TypeScript**: 5.3+
- **Vue**: 3.5+
- **Vite**: 8.3+
- **Element Plus**: 2.14+

## 项目结构

```
frontend/
├── src/
│   ├── types/                 # 类型定义
│   │   ├── index.ts          # 类型索引
│   │   ├── fund.ts           # 基金相关类型
│   │   ├── trade.ts          # 交易相关类型
│   │   ├── ai.ts             # AI分析相关类型
│   │   └── common.ts         # 通用类型
│   ├── views/                # 页面组件
│   │   └── Home.vue          # 首页（TypeScript）
│   ├── router/
│   │   └── index.ts          # 路由配置
│   ├── main.ts               # 入口文件
│   └── App.vue               # 根组件
├── vite.config.ts            # Vite配置
├── tsconfig.json             # TypeScript配置
└── env.d.ts                  # 环境类型声明
```

## 类型定义规范

### 1. 文件组织

每个类型文件包含：
- 文件头注释说明
- `#region` 代码段标记
- 详细的类型注释

### 2. 类型注释规范

```typescript
/**
 * 基金基本信息
 */
export interface FundInfo {
  /** 基金代码，如 '110011' */
  fund_code: string
  /** 基金名称，如 '易方达中小盘混合' */
  fund_name: string
  /** 基金类型：股票型 | 混合型 | 债券型 | 指数型 | 货币型 */
  fund_type: FundType
}
```

### 3. 代码段标记

使用 `#region` 和 `#endregion` 标记代码段：

```typescript
// #region 基金基本信息

/**
 * 基金基本信息
 */
export interface FundInfo {
  // ...
}

// #endregion
```

## 组件开发规范

### 1. Script 标签

```vue
<script setup lang="ts">
// 组件逻辑
</script>
```

### 2. 导入类型

```typescript
import type { FundInfo, AIPortfolio } from '@/types'
```

### 3. 响应式状态

```typescript
/**
 * 加载状态
 */
const loading = ref<boolean>(true)

/**
 * 基金列表
 */
const funds = ref<FundInfo[]>([])
```

### 4. 方法定义

```typescript
/**
 * 加载基金数据
 * @param code - 基金代码
 * @returns 基金信息
 */
const loadFund = async (code: string): Promise<FundInfo | null> => {
  try {
    const response = await axios.get<FundInfo>(`/api/funds/${code}`)
    return response.data
  } catch (error) {
    console.error('加载基金失败:', error)
    return null
  }
}
```

## 类型定义文件说明

### fund.ts - 基金相关类型

| 类型 | 说明 |
|------|------|
| `FundInfo` | 基金基本信息 |
| `FundType` | 基金类型枚举 |
| `FundNav` | 基金净值数据 |
| `FundEstimate` | 基金实时估值 |
| `FundListParams` | 基金列表查询参数 |
| `FundListResponse` | 基金列表响应 |

### trade.ts - 交易相关类型

| 类型 | 说明 |
|------|------|
| `Portfolio` | 投资组合 |
| `Holding` | 持仓信息 |
| `TransactionType` | 交易类型枚举 |
| `Transaction` | 交易记录 |
| `BuyRequest` | 买入请求参数 |
| `SellRequest` | 卖出请求参数 |
| `TradeResponse` | 交易响应 |
| `PortfolioPerformance` | 投资组合表现 |

### ai.ts - AI分析相关类型

| 类型 | 说明 |
|------|------|
| `AIStatus` | AI运行状态 |
| `AIAnalysisStatus` | AI分析状态 |
| `AIDecision` | AI决策类型 |
| `ConfidenceLevel` | 信心水平 |
| `FundAnalysisResult` | 单只基金分析结果 |
| `AIAnalysisResults` | 所有基金分析结果 |
| `AIHolding` | AI持仓信息 |
| `AIPortfolio` | AI持仓 |
| `AITransaction` | AI交易记录 |
| `TechnicalAnalysis` | 技术面分析 |
| `FundamentalAnalysis` | 基本面分析 |
| `NewsAnalysis` | 新闻面分析 |
| `SentimentAnalysis` | 情绪面分析 |
| `AnalysisReport` | 完整分析报告 |
| `WatchListFund` | 观察池基金 |

### common.ts - 通用类型

| 类型 | 说明 |
|------|------|
| `ApiResponse` | 通用API响应 |
| `PaginationParams` | 分页参数 |
| `PaginationResponse` | 分页响应 |
| `TableColumn` | 表格列配置 |
| `ChartDataPoint` | 图表数据点 |
| `FormRule` | 表单验证规则 |
| `LoadingState` | 加载状态 |
| `TimeRange` | 时间范围 |
| `DateFormat` | 日期格式 |

## 常用命令

```bash
# 启动开发服务器
npm run dev

# 类型检查
npm run type-check

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

## 最佳实践

### 1. 使用类型导入

```typescript
// 推荐
import type { FundInfo } from '@/types'

// 不推荐
import { FundInfo } from '@/types'
```

### 2. 明确类型注解

```typescript
// 推荐
const count = ref<number>(0)
const name = ref<string>('')

// 不推荐
const count = ref(0)
const name = ref('')
```

### 3. 使用接口定义对象

```typescript
// 推荐
interface User {
  id: number
  name: string
}
const user = ref<User>({ id: 1, name: '张三' })

// 不推荐
const user = ref({ id: 1, name: '张三' })
```

### 4. 添加详细注释

```typescript
/**
 * 加载基金数据
 * @param code - 基金代码
 * @param limit - 返回数量限制
 * @returns 基金净值数组
 */
const loadFundData = async (code: string, limit: number = 30): Promise<FundNav[]> => {
  // ...
}
```

## 常见问题

### Q: 如何处理第三方库没有类型定义？

A: 创建 `.d.ts` 文件或使用 `any` 类型：

```typescript
// 声明模块
declare module 'some-library' {
  export function someFunction(): void
}

// 或使用 any
const data: any = someLibrary.getData()
```

### Q: 如何在 Vue 组件中使用类型？

A: 使用 `defineProps` 和 `defineEmits`：

```vue
<script setup lang="ts">
interface Props {
  title: string
  count?: number
}

const props = withDefaults(defineProps<Props>(), {
  count: 0
})

const emit = defineEmits<{
  (e: 'update', value: number): void
}>()
</script>
```

---

**文档版本**: v1.0.0
**更新时间**: 2026-09-16