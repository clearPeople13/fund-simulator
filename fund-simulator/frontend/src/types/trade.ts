/**
 * 交易相关类型定义
 * @module types/trade
 */

// #region 投资组合

/**
 * 投资组合
 */
export interface Portfolio {
  /** 组合ID */
  id: number
  /** 用户ID，默认 'default_user' */
  user_id: string
  /** 组合名称 */
  portfolio_name: string
  /** 初始资金 */
  initial_capital: number
  /** 当前可用资金 */
  current_capital: number
  /** 创建时间 */
  created_at: string
}

/**
 * 持仓信息
 */
export interface Holding {
  /** 记录ID */
  id: number
  /** 组合ID */
  portfolio_id: number
  /** 基金代码 */
  fund_code: string
  /** 基金名称 */
  fund_name: string
  /** 基金类型 */
  fund_type: string
  /** 持仓份额 */
  shares: number
  /** 成本价（每份） */
  cost_price: number
  /** 当前净值（每份） */
  current_price: number
  /** 持仓市值 */
  market_value: number
  /** 盈亏金额 */
  profit_loss: number
  /** 盈亏收益率（百分比） */
  profit_loss_rate: number
  /** 创建时间 */
  created_at: string
  /** 更新时间 */
  updated_at: string
}

// #endregion

// #region 交易记录

/**
 * 交易类型
 */
export type TransactionType = 'BUY' | 'SELL' | 'DIVIDEND'

/**
 * 交易记录
 */
export interface Transaction {
  /** 记录ID */
  id: number
  /** 组合ID */
  portfolio_id: number
  /** 基金代码 */
  fund_code: string
  /** 基金名称 */
  fund_name: string
  /** 交易类型：买入 | 卖出 | 分红 */
  transaction_type: TransactionType
  /** 交易金额 */
  amount: number
  /** 交易净值 */
  price: number
  /** 交易份额 */
  shares: number
  /** 手续费 */
  fees: number
  /** 交易日期 */
  transaction_date: string
  /** 备注 */
  notes: string
}

/**
 * 买入请求参数
 */
export interface BuyRequest {
  /** 基金代码 */
  fund_code: string
  /** 买入金额 */
  amount: number
}

/**
 * 卖出请求参数
 */
export interface SellRequest {
  /** 基金代码 */
  fund_code: string
  /** 卖出份额 */
  shares: number
}

/**
 * 交易响应
 */
export interface TradeResponse {
  /** 操作结果消息 */
  message: string
  /** 交易记录ID */
  transaction_id: number
  /** 交易份额 */
  shares: number
  /** 交易净值 */
  price: number
  /** 手续费 */
  fees: number
}

// #endregion

// #region 投资组合统计

/**
 * 投资组合表现
 */
export interface PortfolioPerformance {
  /** 初始资金 */
  initial_capital: number
  /** 当前总资产 */
  current_assets: number
  /** 累计收益 */
  total_return: number
  /** 累计收益率（百分比） */
  total_return_rate: number
  /** 持仓数量 */
  holdings_count: number
}

// #endregion