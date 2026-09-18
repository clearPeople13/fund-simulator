/**
 * AI分析相关类型定义
 * @module types/ai
 */

// #region AI分析状态

/**
 * AI运行状态
 */
export type AIStatus = 'idle' | 'running' | 'completed' | 'error'

/**
 * AI分析状态
 */
export interface AIAnalysisStatus {
  /** 当前状态：空闲 | 运行中 | 完成 | 错误 */
  status: AIStatus
  /** 上次分析时间 */
  lastAnalysis: string | null
  /** 下次分析时间 */
  nextAnalysis: string | null
  /** 分析进度（0-100） */
  progress: number
  /** 当前分析阶段 */
  currentPhase: string
}

// #endregion

// #region AI分析结果

/**
 * AI决策类型
 */
export type AIDecision = 'BUY' | 'SELL' | 'HOLD'

/**
 * 信心水平
 */
export type ConfidenceLevel = '高' | '中等' | '低'

/**
 * 单只基金的AI分析结果
 */
export interface FundAnalysisResult {
  /** 基金代码 */
  fund_code: string
  /** AI决策：买入 | 卖出 | 持有 */
  decision: AIDecision
  /** 信心水平 */
  confidence: ConfidenceLevel
  /** 建议入场价 */
  entry_price: number
  /** 目标价 */
  target_price: string
  /** 止损价 */
  stop_loss: string
  /** 分析时间 */
  analysis_time: string
}

/**
 * 所有基金的AI分析结果
 */
export interface AIAnalysisResults {
  /** 基金代码 -> 分析结果的映射 */
  [fund_code: string]: FundAnalysisResult
}

// #endregion

// #region AI持仓

/**
 * 单只基金的持仓信息
 */
export interface AIHolding {
  /** 持仓份额 */
  shares: number
  /** 成本价（每份） */
  cost: number
  /** 总成本 */
  total_cost: number
}

/**
 * AI持仓信息
 */
export interface AIPortfolio {
  /** 初始资金 */
  initial_capital: number
  /** 当前可用资金 */
  current_capital: number
  /** 持仓详情：基金代码 -> 持仓信息 */
  holdings: Record<string, AIHolding>
  /** 总资产（可用资金 + 持仓市值） */
  total_assets: number
}

// #endregion

// #region AI交易记录

/**
 * AI交易记录
 */
export interface AITransaction {
  /** 交易时间 */
  date: string
  /** 基金代码 */
  fund_code: string
  /** 交易动作：买入 | 卖出 */
  action: 'BUY' | 'SELL'
  /** 交易金额 */
  amount: number
  /** 交易份额 */
  shares: number
  /** 交易净值 */
  price: number
  /** 交易原因 */
  reason: string
}

// #endregion

// #region AI分析报告详情

/**
 * 技术面分析
 */
export interface TechnicalAnalysis {
  /** 评分（0-10） */
  score: number
  /** 趋势：上涨 | 下跌 | 震荡 */
  trend: string
  /** 支撑位 */
  support: string
  /** 阻力位 */
  resistance: string
  /** MACD指标 */
  macd: string
  /** RSI指标 */
  rsi: string
  /** 结论 */
  conclusion: string
}

/**
 * 基本面分析
 */
export interface FundamentalAnalysis {
  /** 评分（0-10） */
  score: number
  /** 市盈率 */
  pe: string
  /** 市净率 */
  pb: string
  /** 净资产收益率 */
  roe: string
  /** 成长率 */
  growth: string
  /** 结论 */
  conclusion: string
}

/**
 * 新闻面分析
 */
export interface NewsAnalysis {
  /** 评分（0-10） */
  score: number
  /** 市场情绪：正面 | 中性 | 负面 */
  sentiment: string
  /** 关键事件 */
  key_events: string
  /** 结论 */
  conclusion: string
}

/**
 * 情绪面分析
 */
export interface SentimentAnalysis {
  /** 评分（0-10） */
  score: number
  /** 资金流向：净流入 | 净流出 */
  fund_flow: string
  /** 机构态度：增持 | 减持 | 不变 */
  institutional: string
  /** 市场热度：高 | 中等 | 低 */
  market_heat: string
  /** 结论 */
  conclusion: string
}

/**
 * 完整的分析报告
 */
export interface AnalysisReport {
  /** 基金代码 */
  fund_code: string
  /** 基金名称 */
  fund_name: string
  /** AI决策 */
  decision: AIDecision
  /** 信心水平 */
  confidence: ConfidenceLevel
  /** 入场价 */
  entry_price: number
  /** 目标价 */
  target_price: string
  /** 止损价 */
  stop_loss: string
  /** 分析时间 */
  analysis_time: string
  /** 技术面分析 */
  technical: TechnicalAnalysis
  /** 基本面分析 */
  fundamental: FundamentalAnalysis
  /** 新闻面分析 */
  news: NewsAnalysis
  /** 情绪面分析 */
  sentiment: SentimentAnalysis
}

// #endregion

// #region AI观察池

/**
 * 观察池基金
 */
export interface WatchListFund {
  /** 基金代码 */
  code: string
  /** 基金名称 */
  name: string
  /** 基金类型 */
  type: string
  /** 最新净值 */
  nav: number
  /** 日涨跌（百分比） */
  change: number
  /** 观察评分（6-10） */
  watchScore: number
  /** 观察原因 */
  watchReason: string
  /** 下次评审时间 */
  nextReview: string
}

// #endregion

// #region API响应

/**
 * AI分析API响应
 */
export interface AIAnalyzeResponse {
  /** 操作结果消息 */
  message: string
  /** 分析结果 */
  results: AIAnalysisResults
  /** 执行的交易 */
  trades: AITransaction[]
  /** 当前持仓 */
  portfolio: AIPortfolio
  /** 分析时间 */
  analysis_time: string
}

// #endregion