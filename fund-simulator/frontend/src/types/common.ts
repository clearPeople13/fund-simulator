/**
 * 通用类型定义
 * @module types/common
 */

// #region API响应

/**
 * 通用API响应结构
 */
export interface ApiResponse<T = any> {
  /** 响应数据 */
  data?: T
  /** 错误信息 */
  error?: string
  /** 操作结果消息 */
  message?: string
}

/**
 * 分页参数
 */
export interface PaginationParams {
  /** 页码，从1开始 */
  page?: number
  /** 每页数量 */
  limit?: number
}

/**
 * 分页响应
 */
export interface PaginationResponse {
  /** 当前页码 */
  page: number
  /** 每页数量 */
  limit: number
  /** 总记录数 */
  total: number
}

// #endregion

// #region 表格相关

/**
 * 表格列配置
 */
export interface TableColumn {
  /** 列字段名 */
  prop: string
  /** 列标题 */
  label: string
  /** 列宽度 */
  width?: number
  /** 最小宽度 */
  minWidth?: number
  /** 是否固定 */
  fixed?: boolean | 'left' | 'right'
  /** 是否可排序 */
  sortable?: boolean
  /** 是否显示溢出提示 */
  showOverflowTooltip?: boolean
}

// #endregion

// #region 图表相关

/**
 * 图表数据点
 */
export interface ChartDataPoint {
  /** X轴值（通常是日期） */
  x: string
  /** Y轴值 */
  y: number
}

/**
 * 图表系列数据
 */
export interface ChartSeries {
  /** 系列名称 */
  name: string
  /** 系列数据 */
  data: number[]
  /** 系列类型 */
  type?: string
  /** 是否平滑 */
  smooth?: boolean
}

// #endregion

// #region 表单相关

/**
 * 表单验证规则
 */
export interface FormRule {
  /** 是否必填 */
  required?: boolean
  /** 提示信息 */
  message: string
  /** 触发方式 */
  trigger: string
  /** 最小长度 */
  min?: number
  /** 最大长度 */
  max?: number
  /** 类型 */
  type?: string
}

// #endregion

// #region 状态相关

/**
 * 加载状态
 */
export interface LoadingState {
  /** 是否加载中 */
  loading: boolean
  /** 错误信息 */
  error: string | null
}

// #endregion

// #region 时间相关

/**
 * 时间范围
 */
export type TimeRange = '1M' | '3M' | '6M' | '1Y' | 'ALL'

/**
 * 日期格式
 */
export type DateFormat = 'YYYY-MM-DD' | 'YYYY/MM/DD' | 'MM-DD' | 'MM/DD'

// #endregion

// #region 通用工具类型

/**
 * 可选字段
 */
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

/**
 * 必填字段
 */
export type Required<T, K extends keyof T> = T & { [P in K]-?: T[P] }

/**
 * 只读字段
 */
export type Readonly<T> = {
  readonly [P in keyof T]: T[P]
}

/**
 * 深度只读
 */
export type DeepReadonly<T> = {
  readonly [P in keyof T]: T[P] extends object ? DeepReadonly<T[P]> : T[P]
}

// #endregion