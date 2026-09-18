/**
 * 基金相关类型定义
 * @module types/fund
 */

// #region 基金基本信息

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
  /** 成立日期，格式：YYYY-MM-DD */
  inception_date: string
  /** 业绩比较基准 */
  benchmark: string
  /** 基金经理 */
  manager: string
  /** 创建时间 */
  created_at: string
}

/**
 * 基金类型枚举
 */
export type FundType = '股票型' | '混合型' | '债券型' | '指数型' | '货币型'

// #endregion

// #region 基金净值数据

/**
 * 基金净值数据
 */
export interface FundNav {
  /** 记录ID */
  id: number
  /** 基金代码 */
  fund_code: string
  /** 净值日期，格式：YYYY-MM-DD */
  nav_date: string
  /** 单位净值 */
  unit_nav: number
  /** 累计净值 */
  acc_nav: number
  /** 日收益率（百分比） */
  daily_return: number
  /** 创建时间 */
  created_at: string
}

/**
 * 基金实时估值
 */
export interface FundEstimate {
  /** 基金代码 */
  fund_code: string
  /** 基金名称 */
  fund_name: string
  /** 估算净值 */
  estimate_nav: number
  /** 估算时间 */
  estimate_time: string
  /** 估算涨幅（百分比） */
  estimate_return: number
  /** 上一交易日净值 */
  last_nav: number
  /** 上一交易日日期 */
  last_date: string
}

// #endregion

// #region 基金列表查询参数

/**
 * 基金列表查询参数
 */
export interface FundListParams {
  /** 基金类型筛选 */
  type?: FundType
  /** 排序字段 */
  sort?: string
  /** 页码，从1开始 */
  page?: number
  /** 每页数量 */
  limit?: number
}

/**
 * 基金列表响应
 */
export interface FundListResponse {
  /** 基金列表 */
  data: FundInfo[]
  /** 分页信息 */
  pagination: {
    /** 当前页码 */
    page: number
    /** 每页数量 */
    limit: number
    /** 总记录数 */
    total: number
  }
}

// #endregion