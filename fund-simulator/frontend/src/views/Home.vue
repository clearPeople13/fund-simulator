<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import axios from 'axios'
import * as echarts from 'echarts'

const loading = ref<boolean>(true)

// 安全的日期格式化函数
// SQLite CURRENT_TIMESTAMP 存储的是 UTC（如 "2026-09-17 06:38:23"，无时区标记），
// 需按 UTC 解析再转本地时间显示；带 Z / 时区偏移的 ISO 字符串原样解析。
const normalizeDateStr = (dateStr: string): string => {
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/.test(dateStr) && !/[zZ]|[+-]\d{2}:\d{2}$/.test(dateStr)) {
    return dateStr.replace(' ', 'T') + 'Z'
  }
  return dateStr.replace(' ', 'T')
}

const formatDate = (dateStr: string | null | undefined): string => {
  if (!dateStr) return '--'
  try {
    const date = new Date(normalizeDateStr(dateStr))
    if (isNaN(date.getTime())) {
      return dateStr
    }
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return dateStr
  }
}

// 判断某条 UTC 时间字符串是否属于今天（本地时区）
// 本地今天 YYYY-MM-DD（模板展示用）
const todayDateStr = (): string => {
  const d = new Date(); const m = String(d.getMonth() + 1).padStart(2, '0'); const day = String(d.getDate()).padStart(2, '0'); return d.getFullYear() + '-' + m + '-' + day
}
const isSameLocalDay = (utcStr: string): boolean => {
  try {
    const d = new Date(normalizeDateStr(utcStr))
    if (isNaN(d.getTime())) return false
    const now = new Date()
    return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && d.getDate() === now.getDate()
  } catch {
    return false
  }
}

// 基金名称
const fundNames: Record<string, string> = {
  '110011': '易方达中小盘混合',
  '161725': '招商中证白酒指数',
  '003834': '华夏能源革新股票',
  '005827': '易方达蓝筹精选混合',
  '005267': '嘉实核心优势股票',
  '001156': '申万菱信新能源汽车',
  '001938': '中欧时代先锋股票',
  '320007': '诺安成长混合',
  '260108': '景顺长城新兴成长混合',
  '519736': '交银优势行业混合'
}

// 用户相关
const currentUser = ref<any>(null)

// 系统状态
const aiStatusDisplay = ref({
  status: 'running',
  startTime: '2026-09-17 00:00:00',
  runningDays: 1,
  lastAnalysis: '等待首次分析...',
  nextAnalysis: '今日 15:00 自动分析'
})

// 核心数据
const portfolio = ref<any>(null)
const holdings = ref<any[]>([])
const transactions = ref<any[]>([])
const pendingTxs = ref<any[]>([]) // 待确认订单（T+1）
const aiStats = ref<any>(null) // AI 经营成绩单
const aiActivity = ref<any[]>([]) // AI 决策轨迹
const hotspots = ref<any>(null) // AI 市场热点分析
const aiCompare = ref<any>(null) // 双经理经营对比
const watchList = ref<any[]>([])
const dailyHistory = ref<any[]>([])

// 每只基金最近一次买入的原始时间（UTC 字符串），用于 T+1 当日收益判断
const lastBuyRaw = new Map<string, string>()

// 观察池数据映射（后端返回真实净值与入场信号）
const mapWatchlist = (data: any[]): any[] => (data || []).map((fund: any) => ({
  code: fund.fund_code,
  fund_code: fund.fund_code,
  name: fund.fund_name || fund.fund_code,
  type: fund.fund_type || '—',
  reason: fund.reason || '',
  source: fund.source || 'manual',
  nav: fund.latest_nav,
  change: fund.daily_return,
  nav_date: fund.nav_date || '',
  change_5d: fund.change_5d,
  change_20d: fund.change_20d,
  drawdown_60d: fund.drawdown_60d,
  above_ma20: fund.above_ma20,
  signal: fund.signal || { action: 'wait', label: '—', reason: '' }
}))

// AI 按当前用户性格自主选基进观察池（系统自动维护，按钮仅作手动刷新）
const discovering = ref(false)
const discoverWatchlist = async (silent = false) => {
  if (discovering.value) return
  discovering.value = true
  try {
    const res = await axios.post('/api/ai/discover-watchlist')
    watchList.value = mapWatchlist(res.data.watchlist)
    if (!silent) message.success(res.data.message || 'AI选基完成')
  } catch (error: any) {
    if (!silent) message.error('AI选基失败: ' + (error.response?.data?.error || error.message))
  } finally {
    discovering.value = false
  }
}

// 信号徽章颜色
const signalClass = (action: string): string => {
  switch (action) {
    case 'buy': return 'signal-buy'
    case 'add': return 'signal-add'
    case 'watch': return 'signal-watch'
    default: return 'signal-wait'
  }
}

// 取消自选
const removeWatch = async (fund: any) => {
  try {
    const res = await axios.delete(`/api/users/${currentUser.value.id}/watchlist/${fund.code}`)
    watchList.value = mapWatchlist(res.data.watchlist)
  } catch (error) {
    console.error('取消自选失败:', error)
  }
}

// 计算属性
const totalAssets = computed(() => {
  // 后端已按真实市值计算 total_assets（现金 + 持仓市值），优先使用；兼容旧数据回退
  if (portfolio.value?.total_assets != null) return portfolio.value.total_assets
  if (!portfolio.value) return 0
  const holdings = portfolio.value.holdings
  if (!holdings || typeof holdings !== 'object') return portfolio.value.current_capital || 0
  const holdingsValue = Object.values(holdings).reduce((sum: number, h: any) => sum + (h?.market_value || h?.total_cost || 0), 0)
  return (portfolio.value.current_capital || 0) + holdingsValue
})

const totalPnl = computed(() => {
  return totalAssets.value - (portfolio.value?.initial_capital || 100000)
})

// 收益构成：已实现盈亏 + 持仓浮动盈亏（累计收益 = 两者之和）
const pnlBreakdown = computed(() => {
  const p = portfolio.value
  if (!p) return { realized: 0, floating: 0, total: 0 }
  const realized = p.realized_pnl || 0
  const hs = holdings.value
  // 浮动盈亏用 loadHoldingsDetail 的 pnl 字段（已处理 T+1 待确认→0），避免待确认基金市值差误入浮动
  const floating = hs.reduce((sum, h) => sum + (h.pnl || 0), 0)
  const total = Math.round((realized + floating) * 100) / 100
  return { realized: Math.round(realized * 100) / 100, floating: Math.round(floating * 100) / 100, total }
})

const totalPnlRate = computed(() => {
  const initial = portfolio.value?.initial_capital || 100000
  return ((totalPnl.value / initial) * 100).toFixed(2)
})

const todayPnl = computed(() => {
  // 优先用后端 portfolio_daily 当日已确认快照（净值未公布时后端返回 null → 待更新）
  if (portfolio.value?.today_pnl != null) return portfolio.value.today_pnl
  // 回退：聚合持仓今日盈亏
  const hs = holdings.value
  if (hs.length === 0) return 0
  // 存在非 T+1 持仓的今日盈亏未更新（当日净值未公布）→ 整体待更新，不显示 0
  const anyUnsettled = hs.some(h => !h.pending_confirm && (h.today_pnl === null || h.today_pnl === undefined))
  if (anyUnsettled) return null
  return hs.reduce((sum, h) => sum + (h.today_pnl ?? 0), 0)
})

// 手动分析状态
const isAnalyzing = ref<boolean>(false)
const analysisProgress = ref<number>(0)
const analysisMessage = ref<string>('')

// 加载数据
const loadAllData = async () => {
  try {
    loading.value = true
    
    // 加载当前用户信息
    const userRes = await axios.get('/api/users/current')
    currentUser.value = userRes.data
    
    // 加载持仓
    const portfolioRes = await axios.get('/api/ai/portfolio')
    portfolio.value = portfolioRes.data
    
    // 加载交易记录
    const txRes = await axios.get('/api/ai/transactions')
    const txData = Array.isArray(txRes.data) ? txRes.data : (txRes.data?.list || [])
    // 记录每只基金最近一次买入的原始时间（用于 T+1 当日收益判断）
    lastBuyRaw.clear()
    for (const tx of txData) {
      if (tx.transaction_type === 'BUY') {
        const prev = lastBuyRaw.get(tx.fund_code)
        if (!prev || tx.transaction_date > prev) lastBuyRaw.set(tx.fund_code, tx.transaction_date)
      }
    }
    pendingTxs.value = (txRes.data && txRes.data.pending) || []
    // AI 经营成绩单 + 决策轨迹
    try {
      const statsRes = await axios.get('/api/ai/stats')
      aiStats.value = statsRes.data
      const actRes = await axios.get('/api/ai/activity', { params: { limit: 12 } })
      aiActivity.value = (actRes.data && actRes.data.list) || []
      // AI 市场热点
      try {
        const hpRes = await axios.get('/api/ai/hotspots')
        hotspots.value = hpRes.data || null
      } catch (e5) { hotspots.value = null }
      // 双经理经营对比
      try {
        const cpRes = await axios.get('/api/ai/compare')
        aiCompare.value = cpRes.data || null
      } catch (e6) { aiCompare.value = null }
      setTimeout(() => initCompareChart(), 300)
    } catch (e4) {
      console.error('加载AI经营数据失败:', e4)
    }
    transactions.value = txData.map((tx: any) => ({
      date: formatDate(tx.transaction_date),
      raw: tx.transaction_date,
      action: tx.transaction_type === 'BUY' ? '买入' : '卖出',
      fund_code: tx.fund_code,
      fund_name: tx.fund_name || fundNames[tx.fund_code] || tx.fund_code,
      amount: tx.amount,
      shares: tx.shares,
      price: tx.price,
      fees: tx.fees || 0,
      reason: tx.reason
    }))
    
    // 加载持仓详情
    await loadHoldingsDetail()

    // 加载持仓基金今日预估涨幅（盘中估值）
    await loadEstimates()
    
    // 加载观察池（真实净值）
    const watchlistRes = await axios.get(`/api/users/${currentUser.value.id}/watchlist`)
    watchList.value = mapWatchlist(watchlistRes.data)
    
    // 加载每日账户快照（资产走势/每日盈亏图真实数据）
    const dailyRes = await axios.get('/api/ai/daily', { params: { user_id: currentUser.value.id } })
    dailyHistory.value = Array.isArray(dailyRes.data) ? dailyRes.data : []
    
    // 加载分析结果
    const aiRes = await axios.get('/api/ai/results')
    if (aiRes.data.lastAnalysis) {
      aiStatusDisplay.value.lastAnalysis = formatDate(aiRes.data.lastAnalysis)
    }
    
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
    setTimeout(() => initCharts(), 100)
    // AI 自主维护观察池：若当前观察池无 AI 推荐项，自动静默补选（无需用户操作）
    setTimeout(() => {
      if (!watchList.value.some((f: any) => f.source === 'ai')) {
        discoverWatchlist(true)
      }
    }, 300)
  }
}

// 加载持仓详情
const loadHoldingsDetail = async () => {
  if (!portfolio.value?.holdings || Object.keys(portfolio.value.holdings).length === 0) {
    holdings.value = []
    return
  }
  
  const holdingsList = []
  for (const [code, holding] of Object.entries(portfolio.value.holdings) as [string, any][]) {
    try {
      // 获取最新2天净值，用于计算今日涨跌幅
      const navRes = await axios.get(`/api/funds/${code}/nav?limit=2`)
      const navData = Array.isArray(navRes.data) ? navRes.data : []
      
      if (navData.length > 0) {
        const latestNav = navData[0]
        const currentPrice = latestNav.unit_nav
        const marketValue = holding.shares * currentPrice
        const pnl = marketValue - holding.total_cost
        const pnlRate = (currentPrice / holding.cost - 1) * 100
        
        // 今日涨跌幅：从API获取的真实数据
        let dailyReturn = latestNav.daily_return || 0
        
        // 如果有两天数据，手动计算涨跌幅
        if (navData.length >= 2) {
          const prevNav = navData[1].unit_nav
          dailyReturn = ((currentPrice - prevNav) / prevNav) * 100
        }
        
        // 基金 T+1 规则：当日买入的份额按当日收盘净值确认，当日无收益
        const rawBuyDate = lastBuyRaw.get(code)
        const pendingConfirm = !!rawBuyDate && isSameLocalDay(rawBuyDate)
        const isTodayNav = isSameLocalDay(latestNav.nav_date + " 00:00:00")
        // 今日盈亏统一口径：份额 × (今日净值 - 昨日净值)（与每日收益明细一致；市值×收益率会多乘(1+收益率)）
        const prevNav = navData.length >= 2 ? navData[1].unit_nav : null
        const todayPnl = pendingConfirm ? 0 : (isTodayNav && prevNav != null ? holding.shares * (currentPrice - prevNav) : null)
        
        holdingsList.push({
          fund_code: code,
          fund_name: holding.fund_name || fundNames[code] || code,
          shares: holding.shares,
          cost_price: holding.cost,
          current_price: currentPrice,
          market_value: marketValue,
          total_cost: holding.total_cost,
          pnl: pendingConfirm ? 0 : pnl,
          pnl_rate: pendingConfirm ? 0 : pnlRate,
          daily_return: dailyReturn,
          today_pnl: todayPnl,
          pending_confirm: pendingConfirm,
          latest_date: latestNav.nav_date || '--'
        })
      } else {
        // 无净值数据
        holdingsList.push({
          fund_code: code,
          fund_name: holding.fund_name || fundNames[code] || code,
          shares: holding.shares,
          cost_price: holding.cost,
          current_price: null,
          market_value: null,
          total_cost: holding.total_cost,
          pnl: null,
          pnl_rate: null,
          daily_return: null,
          today_pnl: null,
          latest_date: '无数据'
        })
      }
    } catch (error) {
      console.error(`获取基金 ${code} 数据失败:`, error)
      holdingsList.push({
        fund_code: code,
        fund_name: holding.fund_name || fundNames[code] || code,
        shares: holding.shares,
        cost_price: holding.cost,
        current_price: null,
        market_value: null,
        total_cost: holding.total_cost,
        pnl: null,
        pnl_rate: null,
        daily_return: null,
        today_pnl: null,
        latest_date: '获取失败'
      })
    }
  }
  
  holdings.value = holdingsList
}

// 初始化图表
// 资产配置环形图：各持仓市值 + 现金占比
const initAllocChart = () => {
  const el = document.getElementById('allocChart')
  if (!el) return
  const chart = echarts.getInstanceByDom(el) || echarts.init(el)
  const hs = holdings.value
  const cash = portfolio.value?.current_capital || 0
  const items = hs.map(h => ({ name: h.fund_name || h.fund_code, value: Math.round((h.market_value || 0) * 100) / 100 }))
  items.push({ name: '现金', value: Math.round(cash * 100) / 100 })
  chart.setOption({
    color: ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#f43f5e', '#64748b'],
    tooltip: { trigger: 'item', formatter: (p: any) => `${p.name}: ¥${Number(p.value).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}（${p.percent}%）` },
    legend: { bottom: 0, textStyle: { color: '#94a3b8', fontSize: 12 }, itemWidth: 12, itemHeight: 12 },
    series: [{
      type: 'pie', radius: ['46%', '72%'], center: ['50%', '44%'],
      itemStyle: { borderRadius: 6, borderColor: '#131a35', borderWidth: 2 },
      label: { color: '#cbd5e1', fontSize: 11, formatter: '{b}\n{d}%' },
      data: items
    }],
    grid: { containLabel: true }
  })
}

const initCharts = () => {
  initAssetChart()
  initPnlChart()
  initAllocChart()
}

// 资产走势图（真实每日快照数据）
const initAssetChart = () => {
  const chartDom = document.getElementById('assetChart')
  if (!chartDom) return
  
  const existingChart = echarts.getInstanceByDom(chartDom)
  if (existingChart) existingChart.dispose()
  
  const data = dailyHistory.value
  // 数据不足时不造假：显示真实状态说明
  if (data.length < 2) {
    chartDom.innerHTML = `<div class="chart-empty">
      <div class="empty-icon">📈</div>
      <p>系统自 ${data[0]?.date || '今日'} 开始记录，暂无历史资产走势</p>
      <p class="chart-empty-sub">当前总资产 ¥${totalAssets.value.toLocaleString()}（运行第 ${data.length || 1} 天）</p>
    </div>`
    return
  }
  
  const dates = data.map(d => d.date.slice(5).replace('-', '/'))
  const values = data.map(d => Math.round(d.total_assets))
  
  const myChart = echarts.init(chartDom)
  myChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e0e0e0',
      textStyle: { color: '#333' },
      formatter: function(params: any) {
        if (params && params[0]) {
          const d = data[params[0].dataIndex]
          return `${d.date}<br/>总资产: <b>¥${d.total_assets.toLocaleString()}</b><br/>现金: ¥${d.cash.toLocaleString()} / 持仓: ¥${d.market_value.toLocaleString()}`
        }
        return ''
      }
    },
    grid: { top: 20, right: 20, bottom: 30, left: 80 },
    xAxis: { 
      type: 'category', 
      data: dates,
      axisLine: { lineStyle: { color: '#e0e0e0' } },
      axisLabel: { color: '#999', fontSize: 11 }
    },
    yAxis: { 
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f0f0f0' } },
      axisLabel: { color: '#999', formatter: '¥{value}' }
    },
    series: [{
      type: 'line',
      data: values,
      smooth: true,
      symbol: 'none',
      lineStyle: { color: '#6366f1', width: 2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(99, 102, 241, 0.15)' },
          { offset: 1, color: 'rgba(99, 102, 241, 0.02)' }
        ])
      }
    }]
  })
  
  window.addEventListener('resize', () => myChart.resize())
}

// 每日盈亏图（真实每日快照数据）
const initPnlChart = () => {
  const chartDom = document.getElementById('pnlChart')
  if (!chartDom) return
  
  const existingChart = echarts.getInstanceByDom(chartDom)
  if (existingChart) existingChart.dispose()
  
  const data = dailyHistory.value
  // 数据不足时不造假：显示真实状态说明
  if (data.length < 2) {
    chartDom.innerHTML = `<div class="chart-empty">
      <div class="empty-icon">📊</div>
      <p>系统自 ${data[0]?.date || '今日'} 开始记录，暂无每日盈亏历史</p>
      <p class="chart-empty-sub">今日盈亏 ${todayPnl.value === null ? '待更新（今日净值 21:30 公布后更新）' : (todayPnl.value >= 0 ? '+' : '') + '¥' + todayPnl.value.toFixed(2)}（当日买入按 T+1 确认，次日开始计盈亏）</p>
    </div>`
    return
  }
  
  const dates = data.map(d => d.date.slice(5).replace('-', '/'))
  const pnlData = data.map(d => Math.round(d.daily_pnl))
  
  const myChart = echarts.init(chartDom)
  myChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e0e0e0',
      textStyle: { color: '#333' },
      formatter: function(params: any) {
        if (params && params[0]) {
          const d = data[params[0].dataIndex]
          const value = d.daily_pnl
          const color = value >= 0 ? '#10b981' : '#ef4444'
          return d.date + '<br/>盈亏: <span style="color:' + color + '">¥' + (value >= 0 ? '+' : '') + value.toFixed(2) + '</span>'
        }
        return ''
      }
    },
    grid: { top: 20, right: 20, bottom: 30, left: 80 },
    xAxis: { 
      type: 'category', 
      data: dates,
      axisLine: { lineStyle: { color: '#e0e0e0' } },
      axisLabel: { color: '#999', fontSize: 11 }
    },
    yAxis: { 
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f0f0f0' } },
      axisLabel: { color: '#999', formatter: '¥{value}' }
    },
    series: [{
      type: 'bar',
      data: pnlData.map(value => ({
        value: value,
        itemStyle: {
          color: value >= 0 ? '#10b981' : '#ef4444',
          borderRadius: value >= 0 ? [4, 4, 0, 0] : [0, 0, 4, 4]
        }
      })),
      barWidth: '60%'
    }]
  })
  
  window.addEventListener('resize', () => myChart.resize())
}

// 手动触发分析
const triggerManualAnalysis = async () => {
  if (isAnalyzing.value) return
  
  isAnalyzing.value = true
  analysisProgress.value = 0
  analysisMessage.value = '正在准备分析...'
  
  try {
    const steps = [
      { progress: 10, message: '获取基金数据...' },
      { progress: 30, message: '技术面分析...' },
      { progress: 50, message: '基本面分析...' },
      { progress: 70, message: '情绪面分析...' },
      { progress: 90, message: '生成交易决策...' },
      { progress: 100, message: '分析完成！' }
    ]
    
    for (const step of steps) {
      analysisProgress.value = step.progress
      analysisMessage.value = step.message
      await new Promise(resolve => setTimeout(resolve, 500))
    }
    
    // 只分析观察池中的标的（观察池 = AI 选股池，无观察则不入场）
    const fundCodes = watchList.value.map((f) => f.code)
    
    const analyzeRes = await axios.post('/api/ai/analyze', {
      fund_codes: fundCodes,
      user_id: currentUser.value?.id || 'default'
    })
    
    analysisMessage.value = analyzeRes.data?.message || '分析完成！'
    await loadAllData()
    
    setTimeout(() => {
      isAnalyzing.value = false
      analysisProgress.value = 0
      analysisMessage.value = ''
    }, 2000)
    
  } catch (error) {
    console.error('分析失败:', error)
    analysisMessage.value = '分析失败，请重试'
    isAnalyzing.value = false
  }
}

// 加载持仓基金今日预估涨幅（/api/portfolio/estimates 批量估值，合并到 holdings）
const loadEstimates = async () => {
  try {
    const codes = holdings.value.map((h: any) => h.fund_code).join(',')
    if (!codes) return
    const res = await axios.get('/api/portfolio/estimates', { params: { codes } })
    const map = res.data || {}
    holdings.value = holdings.value.map((h: any) => {
      const e = map[h.fund_code]
      return {
        ...h,
        estimate_return: e && e.estimate_return !== null && e.estimate_return !== undefined ? e.estimate_return : null,
        estimate_time: e && e.estimate_time ? e.estimate_time : '',
        estimate_available: !!(e && e.estimate_available)
      }
    })
  } catch (err: any) {
    console.warn('加载预估涨幅失败:', err.message)
  }
}

// 基金详情弹窗（持仓明细/观察池 → 弹窗：操作记录时间线 + 基金信息，不再跳页）
const detailVisible = ref<boolean>(false)
const detailLoading = ref<boolean>(false)
const detailFund = ref<any>(null)
const detailTxs = ref<any[]>([])
const detailNavList = ref<any[]>([]) // 升序 [{date, nav}]
const detailDailyPnl = ref<any[]>([]) // 每日收益明细 [{date, nav, daily_return, shares, pnl}]
const detailFees = ref<any>(null) // 基金真实费率（fund_fees）

// 查看基金详情（弹窗：涨幅折线图 + 买卖节点 + 基金信息）
const viewFundDetail = async (fund: any) => {
  const code = fund?.fund_code || fund?.code || fund?.fundCode
  if (!code) return
  detailVisible.value = true
  detailLoading.value = true
  detailTxs.value = transactions.value
    .filter((tx: any) => tx.fund_code === code)
    .slice()
    .sort((a: any, b: any) => String(a.raw || '').localeCompare(String(b.raw || '')))
  detailFund.value = { code, name: fund?.fund_name || fund?.name || code }
  try {
    // 净值历史（接口倒序 → 升序 unit_nav，供涨幅曲线）
    const navRes = await axios.get(`/api/funds/${code}/nav`, { params: { limit: 300 } })
    const navRows = Array.isArray(navRes.data) ? navRes.data : []
    detailNavList.value = navRows
      .map((n: any) => ({ date: n.nav_date, nav: n.unit_nav, daily_return: n.daily_return }))
      .filter((n: any) => n.date && n.nav != null)
      .reverse()
    // 每日收益明细（日期/当日涨幅/当日盈亏金额）
    try {
      const dailyPnlRes = await axios.get('/api/ai/fund-daily-pnl', { params: { fund_code: code } })
      detailDailyPnl.value = (dailyPnlRes.data && dailyPnlRes.data.data) || []
    } catch (e2) {
      detailDailyPnl.value = []
    }
    // 费率详情（真实 fund_fees：申购/赎回阶梯/管理/托管）
    try {
      const feeRes = await axios.get('/api/ai/fund-fees', { params: { fund_code: code } })
      detailFees.value = (feeRes.data && feeRes.data.found) ? feeRes.data : null
    } catch (e4) {
      detailFees.value = null
    }
    // 基金基本信息（/api/funds/:code 查 funds 表，含经理/成立日期/基准；列表接口查 fund_universe 无这些字段）
    try {
      const fundRes = await axios.get(`/api/funds/${code}`)
      const info = fundRes.data
      if (info && info.fund_code) {
        detailFund.value = {
          code: info.fund_code,
          name: info.fund_name,
          type: info.fund_type,
          manager: info.manager,
          inception_date: info.inception_date,
          benchmark: info.benchmark
        }
      }
    } catch (e3) {
      console.error('加载基金信息失败:', e3)
    }
  } catch (error) {
    console.error('加载基金详情失败:', error)
  } finally {
    detailLoading.value = false
    setTimeout(() => initDetailChart(), 120)
  }
}

// 双经理每日资产对比图
const initCompareChart = () => {
  const dom = document.getElementById('compareChart')
  if (!dom || !aiCompare.value || !aiCompare.value.daily.length) return
  const daily = aiCompare.value.daily
  const u0 = aiCompare.value.users[0]
  const u1 = aiCompare.value.users[1]
  if (!u0 || !u1) return
  const chart = echarts.init(dom)
  chart.setOption({
    backgroundColor: 'transparent',
    grid: { left: 70, right: 20, top: 36, bottom: 30 },
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(15,20,40,0.95)', borderColor: 'rgba(99,102,241,0.4)', textStyle: { color: '#e2e8f0', fontSize: 12 }, valueFormatter: (v: any) => (v == null ? '—' : '¥' + Number(v).toLocaleString()) },
    legend: { top: 0, textStyle: { color: '#94a3b8', fontSize: 12 }, data: [u0.name, u1.name] },
    xAxis: { type: 'category', data: daily.map((d: any) => d.date), axisLine: { lineStyle: { color: 'rgba(148,163,184,0.3)' } }, axisLabel: { color: '#94a3b8', fontSize: 11, hideOverlap: true } },
    yAxis: { type: 'value', name: '总资产', nameTextStyle: { color: '#94a3b8' }, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.12)' } }, axisLabel: { color: '#94a3b8', formatter: (v: any) => (v / 10000).toFixed(1) + '万' } },
    series: [
      { name: u0.name, type: 'line', smooth: true, symbol: 'circle', symbolSize: 5, lineStyle: { color: '#34d399', width: 2 }, itemStyle: { color: '#34d399' }, data: daily.map((d: any) => d[u0.id]) },
      { name: u1.name, type: 'line', smooth: true, symbol: 'circle', symbolSize: 5, lineStyle: { color: '#fbbf24', width: 2 }, itemStyle: { color: '#fbbf24' }, data: daily.map((d: any) => d[u1.id]) }
    ]
  })
}

// 热点状态徽章样式
const hotspotBadge = (o: string) => {
  if (o.includes('爆发')) return 'hotspot-hot'
  if (o.includes('启动')) return 'hotspot-warm'
  if (o.includes('走强')) return 'hotspot-mild'
  if (o.includes('退潮') || o.includes('防御')) return 'hotspot-cold'
  return 'hotspot-mild'
}

// 操作明细列表：每笔交易的当日涨幅率 + 实际金额变动 + 收益（买入=剩余份额浮盈亏，卖出=已实现盈亏；平均成本法）
const detailRows = computed(() => {
  const txs = detailTxs.value.slice().sort((a: any, b: any) => String(a.raw || '').localeCompare(String(b.raw || '')))
  // 平均成本价 = total_cost / 当前份额（与账户口径一致）
  const hold = holdings.value.find((h: any) => h.fund_code === detailFund.value?.code)
  const avgCost = hold && hold.shares > 0 ? hold.total_cost / hold.shares : 0
  const curNav = hold ? hold.current_price : null
  // FIFO 扣减：每笔买入的剩余在持份额（卖出按买入先后扣减）
  const leftMap = new Map<string, number>()
  txs.forEach((t: any) => { if (t.action === '买入') leftMap.set(t.raw, Number(t.shares) || 0) })
  for (const t of txs) {
    if (t.action !== '卖出') continue
    let toSell = Number(t.shares) || 0
    for (const b of txs) {
      if (b.action !== '买入' || toSell <= 0) continue
      const left = leftMap.get(b.raw) || 0
      if (left <= 0) continue
      const cut = Math.min(left, toSell)
      leftMap.set(b.raw, left - cut)
      toSell -= cut
    }
  }
  return txs.map((tx: any) => {
    const day = String(tx.date).slice(0, 10).replace(/\//g, '-')
    const navRow = detailNavList.value.find((n: any) => n.date === day)
    const isBuy = tx.action === '买入'
    const cash_change = isBuy ? -tx.amount : (tx.amount - (tx.fees || 0))
    let pnl: number | null = null
    let pnlRate: number | null = null
    let pnlTag = ''
    if (isBuy) {
      // 买入：剩余在持份额的浮盈亏（现价 - 平均成本）
      const left = leftMap.get(tx.raw) || 0
      pnl = curNav != null ? (curNav - avgCost) * left : null
      pnlRate = pnl != null && avgCost > 0 && left > 0 ? (pnl / (avgCost * left)) * 100 : null
      pnlTag = '浮'
    } else {
      // 卖出：已实现盈亏优先取系统账本 realized_pnl（精确对账）；无账本时按平均成本估算
      const realized = hold && hold.realized_pnl != null ? hold.realized_pnl : null
      const cost = avgCost * tx.shares
      pnl = realized != null ? realized : (cost > 0 ? (tx.amount - (tx.fees || 0)) - cost : null)
      pnlRate = pnl != null && cost > 0 ? (pnl / cost) * 100 : null
      pnlTag = '实'
    }
    return { ...tx, day, daily_return: navRow ? navRow.daily_return : null, cash_change, pnl, pnl_rate: pnlRate, pnl_tag: pnlTag }
  })
})

// 收益汇总：已实现（卖出）/持有浮盈（买入剩余）/该基金合计
const detailPnlSummary = computed(() => {
  const rows = detailRows.value
  const realized = rows.filter((r: any) => r.action === '卖出').reduce((s: number, r: any) => s + (r.pnl ?? 0), 0)
  const floating = rows.filter((r: any) => r.action === '买入').reduce((s: number, r: any) => s + (r.pnl ?? 0), 0)
  return { realized, floating, total: realized + floating }
})

// 涨幅折线图（最近 120 交易日，以起点净值为 0 基准；买入▲绿/卖出▼红节点全部标记，悬浮显示买卖详情）
const initDetailChart = () => {
  const chartDom = document.getElementById('detailChart')
  if (!chartDom) return
  const existing = echarts.getInstanceByDom(chartDom)
  if (existing) existing.dispose()
  const navList = detailNavList.value
  const txs = detailTxs.value
  if (!navList.length || !txs.length) return

  // 净值序列（升序），交易确认日若不在净值序列中（如当日卖出、净值未公布）则追加到末尾，值用确认净值/末值
  const dates: string[] = []
  const navs: number[] = []
  for (const n of navList) { dates.push(n.date); navs.push(n.nav) }
  for (const tx of txs) {
    const day = String(tx.date).slice(0, 10).replace(/\//g, '-')
    if (!dates.includes(day)) {
      dates.push(day)
      navs.push(Number(tx.price) || navs[navs.length - 1])
    }
  }
  // 最近 120 个点（含追加的交易日）
  const startIdx = Math.max(0, dates.length - 120)
  const sDates = dates.slice(startIdx)
  const sNavs = navs.slice(startIdx)
  const baseNav = sNavs[0] || 1
  const rets = sNavs.map((v: number) => (v / baseNav - 1) * 100)
  const dateIdx = new Map(sDates.map((d: string, i: number) => [d, i]))

  // 买卖节点：买入▲绿 / 卖出▼红，全部交易记录都要有节点
  const marks: any[] = []
  for (const tx of txs) {
    const day = String(tx.date).slice(0, 10).replace(/\//g, '-')
    const i = dateIdx.get(day)
    if (i == null) continue
    const isBuy = tx.action === '买入'
    const hasNav = navList.some((n: any) => n.date === day)
    marks.push({
      name: isBuy ? '买入' : '卖出',
      coord: [day, rets[i]],
      symbol: 'triangle',
      symbolRotate: isBuy ? 0 : 180,
      symbolSize: 18,
      itemStyle: { color: isBuy ? '#34d399' : '#f87171', borderColor: '#0d1330', borderWidth: 2 },
      label: { show: true, formatter: isBuy ? '买' : '卖', fontSize: 12, fontWeight: 700, color: '#ffffff' },
      _action: isBuy ? '买入' : '卖出',
      _date: tx.date,
      _shares: Number(tx.shares) || 0,
      _price: Number(tx.price) || 0,
      _fees: Number(tx.fees) || 0,
      _pending: !hasNav
    })
  }

  const myChart = echarts.init(chartDom)
  myChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 20, 48, 0.92)',
      borderWidth: 0,
      textStyle: { color: '#e8ebff', fontSize: 12 },
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params
        if (!p || p.axisValue == null) return ''
        const v = Number(p.value)
        return `${p.axisValue}<br/>涨幅 ${v >= 0 ? '+' : ''}${v.toFixed(2)}%`
      }
    },
    grid: { left: 54, right: 18, top: 32, bottom: 30 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: sDates,
      axisLine: { lineStyle: { color: '#2c3466' } },
      axisLabel: { color: '#8b92b8', fontSize: 11, interval: (idx: number) => idx === 0 || idx === sDates.length - 1 || idx % Math.max(1, Math.floor(sDates.length / 8)) === 0 },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: { color: '#8b92b8', fontSize: 11, formatter: '{value}%' },
      splitLine: { lineStyle: { color: '#232b55' } }
    },
    series: [{
      name: '涨幅',
      type: 'line',
      smooth: true,
      symbol: 'none',
      data: rets,
      lineStyle: { color: '#667eea', width: 2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(102, 126, 234, 0.28)' },
          { offset: 1, color: 'rgba(102, 126, 234, 0.03)' }
        ])
      },
      markPoint: {
        symbolOffset: [0, -10],
        data: marks,
        tooltip: {
          formatter: (p: any) => {
            const d = p && p.data
            if (!d) return ''
            const pending = d._pending ? '（净值待更新）' : ''
            return `${d._action} · ${d._date}${pending}<br/>份额 ${d._shares.toLocaleString()} 份<br/>净值 ¥${d._price.toFixed(4)} · 手续费 ¥${d._fees.toFixed(2)}`
          }
        }
      }
    }]
  })
  window.addEventListener('resize', () => myChart.resize())
}

onMounted(() => {
  loadAllData()
})
</script>

<template>
  <a-spin :spinning="loading">
  <div class="dashboard">
    <!-- 用户信息栏 -->
    <div class="user-bar" v-if="currentUser">
      <div class="user-bar-left">
        <span class="user-bar-avatar">{{ currentUser.avatar }}</span>
        <div class="user-bar-info">
          <span class="user-bar-name">{{ currentUser.name }}</span>
          <span class="user-bar-desc">{{ currentUser.description }}</span>
        </div>
      </div>
      <div class="user-bar-right">
        <div class="user-bar-stat">
          <span class="stat-label">目标收益</span>
          <span class="stat-value">{{ (currentUser.target_return * 100) }}%</span>
        </div>
        <div class="user-bar-stat">
          <span class="stat-label">止损线</span>
          <span class="stat-value">{{ (currentUser.stop_loss * 100) }}%</span>
        </div>
      </div>
    </div>

    <!-- 状态栏 -->
    <div class="status-bar">
      <div class="status-left">
        <div class="status-dot" :class="{ analyzing: isAnalyzing }"></div>
        <span class="status-text">{{ isAnalyzing ? '分析中...' : 'AI 运行中' }}</span>
        <span class="status-divider">|</span>
        <span class="status-info">上次分析：{{ aiStatusDisplay.lastAnalysis }}</span>
      </div>
      <div class="status-right">
        <span class="next-analysis">下次分析：{{ aiStatusDisplay.nextAnalysis }}</span>
        <button 
          class="refresh-btn" 
          :class="{ disabled: isAnalyzing }"
          @click="triggerManualAnalysis"
          :disabled="isAnalyzing"
        >
          <span class="refresh-icon" :class="{ spinning: isAnalyzing }">🔄</span>
          {{ isAnalyzing ? '分析中' : '立即分析' }}
        </button>
      </div>
    </div>

    <!-- 分析进度条 -->
    <div v-if="isAnalyzing" class="analysis-progress-bar">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: analysisProgress + '%' }"></div>
      </div>
      <div class="progress-text">{{ analysisMessage }} ({{ analysisProgress }}%)</div>
    </div>

    <!-- 资产总览卡片 -->
    <div class="overview-cards">
      <div class="overview-card primary">
        <div class="card-icon">💰</div>
        <div class="card-content">
          <div class="card-label">总资产</div>
          <div class="card-value">¥{{ totalAssets.toLocaleString() }}</div>
        </div>
      </div>
      <div class="overview-card" :class="todayPnl === null ? 'info' : (todayPnl >= 0 ? 'success' : 'danger')">
        <div class="card-icon">📈</div>
        <div class="card-content">
          <div class="card-label">今日盈亏</div>
          <div class="card-value">
            <template v-if="todayPnl === null"><span class="nav-date">待更新</span></template>
            <template v-else>{{ todayPnl >= 0 ? '+' : '' }}¥{{ todayPnl.toFixed(2) }}</template>
          </div>
          <div class="card-sub" v-if="todayPnl === null">今日净值 21:30 公布后更新</div>
        </div>
      </div>
      <div class="overview-card" :class="totalPnl >= 0 ? 'success' : 'danger'">
        <div class="card-icon">🎯</div>
        <div class="card-content">
          <div class="card-label">累计收益</div>
          <div class="card-value">{{ totalPnl >= 0 ? '+' : '' }}¥{{ totalPnl.toFixed(2) }}</div>
        </div>
      </div>
      <div class="overview-card" :class="parseFloat(totalPnlRate) >= 0 ? 'success' : 'danger'">
        <div class="card-icon">📊</div>
        <div class="card-content">
          <div class="card-label">收益率</div>
          <div class="card-value">{{ parseFloat(totalPnlRate) >= 0 ? '+' : '' }}{{ totalPnlRate }}%</div>
        </div>
      </div>
      <div class="overview-card info">
        <div class="card-icon">💵</div>
        <div class="card-content">
          <div class="card-label">可用资金</div>
          <div class="card-value">¥{{ (portfolio?.current_capital || 0).toLocaleString() }}</div>
        </div>
      </div>
      <div class="overview-card warning">
        <div class="card-icon">📦</div>
        <div class="card-content">
          <div class="card-label">持仓数量</div>
          <div class="card-value">{{ holdings.length }} 只</div>
        </div>
      </div>
    </div>

    <!-- 收益构成：累计收益 = 已实现 + 浮动 -->
    <div class="pnl-breakdown">
      <div class="bd-item">
        <span class="bd-label">已实现盈亏</span>
        <span :class="pnlBreakdown.realized >= 0 ? 'profit' : 'loss'">
          <template v-if="pnlBreakdown.realized >= 0">+</template>¥{{ pnlBreakdown.realized.toFixed(2) }}
        </span>
      </div>
      <div class="bd-item">
        <span class="bd-label">持仓浮动盈亏</span>
        <span :class="pnlBreakdown.floating >= 0 ? 'profit' : 'loss'">
          <template v-if="pnlBreakdown.floating >= 0">+</template>¥{{ pnlBreakdown.floating.toFixed(2) }}
        </span>
      </div>
      <div class="bd-item bd-total">
        <span class="bd-label">累计收益（已实现 + 浮动）</span>
        <span :class="pnlBreakdown.total >= 0 ? 'profit' : 'loss'">
          <template v-if="pnlBreakdown.total >= 0">+</template>¥{{ pnlBreakdown.total.toFixed(2) }}
        </span>
      </div>
    </div>

    <!-- AI 经营成绩单：AI 按现实基金操作法经营账户的量化成绩 -->
    <div v-if="aiStats" class="ai-score-card">
      <div class="score-head">
        <span class="score-title">🤖 AI 经营成绩单</span>
        <span class="score-sub">决策统计 · 全自动，用户只读</span>
      </div>
      <div class="score-grid">
        <div class="score-item">
          <div class="s-label">交易笔数</div>
          <div class="s-value">{{ aiStats.total_trades }} <small>（买{{ aiStats.buy_count }} / 卖{{ aiStats.sell_count }}）</small></div>
        </div>
        <div class="score-item">
          <div class="s-label">已实现盈亏</div>
          <div class="s-value" :class="aiStats.realized_pnl >= 0 ? 'profit' : 'loss'">
            <template v-if="aiStats.realized_pnl >= 0">+</template>¥{{ aiStats.realized_pnl.toFixed(2) }}
          </div>
        </div>
        <div class="score-item">
          <div class="s-label">卖出胜率</div>
          <div class="s-value">{{ aiStats.win_rate }}% <small>（{{ aiStats.win_count }}/{{ aiStats.realized_count }} 笔）</small></div>
        </div>
        <div class="score-item">
          <div class="s-label">平均持有</div>
          <div class="s-value">{{ aiStats.avg_hold_days }} 天</div>
        </div>
        <div class="score-item">
          <div class="s-label">风控执行</div>
          <div class="s-value">
            <span class="risk-tag">止损 {{ aiStats.stop_loss_count }}</span>
            <span class="risk-tag">止盈 {{ aiStats.stop_profit_count }}</span>
            <span class="risk-tag">减仓 {{ aiStats.reduce_count }}</span>
          </div>
        </div>
        <div class="score-item">
          <div class="s-label">建仓节奏</div>
          <div class="s-value">加仓 {{ aiStats.add_count }} 次 · 再平衡 {{ aiStats.rebalance_count }} 次</div>
        </div>
        <div class="score-item">
          <div class="s-label">盯盘规模</div>
          <div class="s-value">观察池 {{ aiStats.watchlist_count }} 只 · 已分析 {{ aiStats.analysis_rounds }} 轮</div>
        </div>
        <div class="score-item">
          <div class="s-label">累计手续费</div>
          <div class="s-value">¥{{ (aiStats.buy_fee + (0)).toFixed(2) }}</div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <div class="chart-card">
        <div class="chart-header">
          <h3>📈 资产走势</h3>
          <div class="chart-tabs">
            <span class="tab active">30天</span>
            <span class="tab">90天</span>
            <span class="tab">全部</span>
          </div>
        </div>
        <div id="assetChart" class="chart-container"></div>
      </div>
      <div class="chart-card">
        <div class="chart-header">
          <h3>📊 每日盈亏</h3>
        </div>
        <div id="pnlChart" class="chart-container"></div>
      </div>
      <div class="chart-card">
        <div class="chart-header">
          <h3>🥧 资产配置</h3>
          <span class="nav-date">持仓市值 + 现金占比</span>
        </div>
        <div id="allocChart" class="chart-container"></div>
      </div>
    </div>

    <!-- 持仓明细表格 -->
    <div class="card">
      <div class="card-header">
        <h3>📋 持仓明细</h3>
        <span class="badge success">{{ holdings.length }} 只基金</span>
      </div>
      <div class="card-body">
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>基金代码</th>
                <th>基金名称</th>
                <th>持仓份额</th>
                <th>成本价</th>
                <th>现价 / 净值日</th>
                <th>市值</th>
                <th>日涨跌</th>
                <th>预估今日</th>
                <th>今日盈亏</th>
                <th>累计盈亏</th>
                <th>收益率</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="holding in holdings" :key="holding.fund_code">
                <td class="code">{{ holding.fund_code }}</td>
                <td class="name">{{ holding.fund_name }}</td>
                <td class="number">{{ holding.shares.toLocaleString() }}</td>
                <td class="number">¥{{ holding.cost_price.toFixed(4) }}</td>
                <td class="number">¥{{ holding.current_price.toFixed(4) }} <span class="nav-date">{{ holding.latest_date }}</span></td>
                <td class="number">¥{{ holding.market_value.toFixed(2) }}</td>
                <td :class="holding.daily_return >= 0 ? 'profit' : 'loss'">
                  <template v-if="holding.pending_confirm">—</template>
                  <template v-else-if="holding.daily_return !== null">
                    {{ holding.daily_return >= 0 ? '+' : '' }}{{ holding.daily_return.toFixed(2) }}%<span class="nav-date" v-if="holding.latest_date !== todayDateStr()">({{ holding.latest_date }})</span>
                  </template>
                  <template v-else>--</template>
                </td>
                <td :class="(holding.estimate_return ?? 0) >= 0 ? 'profit' : 'loss'">
                  <template v-if="holding.estimate_available && holding.estimate_return !== null">
                    {{ holding.estimate_return >= 0 ? '+' : '' }}{{ holding.estimate_return.toFixed(2) }}%
                    <a-tooltip v-if="holding.estimate_time" :title="'估值时间 ' + holding.estimate_time">
                      <span class="nav-date est-time">{{ holding.estimate_time.slice(11, 16) }}</span>
                    </a-tooltip>
                  </template>
                  <template v-else><span class="nav-date">—</span></template>
                </td>
                <td :class="holding.today_pnl >= 0 ? 'profit' : 'loss'">
                  <template v-if="holding.pending_confirm">
                    +¥0.00
                    <span class="t1-tag" title="T+1 规则：当日买入按当日收盘净值确认，次日开始计算收益">T+1</span>
                  </template>
                  <template v-else-if="holding.today_pnl !== null">
                    {{ holding.today_pnl >= 0 ? '+' : '' }}¥{{ holding.today_pnl.toFixed(2) }}
                  </template>
                  <template v-else><span class="nav-date">净值待更新</span><span class="t1-tag" title="今日净值 21:30 公布后更新">今日</span></template>
                </td>
                <td :class="holding.pnl >= 0 ? 'profit' : 'loss'">
                  <template v-if="holding.pending_confirm">— <span class="t1-tag" title="T+1 规则：当日买入按当日收盘净值确认，次日开始计算盈亏">T+1</span></template><template v-else-if="holding.pnl !== null">
                    {{ holding.pnl >= 0 ? '+' : '' }}¥{{ holding.pnl.toFixed(2) }}
                  </template>
                  <template v-else>--</template>
                </td>
                <td :class="holding.pnl_rate >= 0 ? 'profit' : 'loss'">
                  <template v-if="holding.pending_confirm">—</template><template v-else-if="holding.pnl_rate !== null">
                    {{ holding.pnl_rate >= 0 ? '+' : '' }}{{ holding.pnl_rate.toFixed(2) }}%
                  </template>
                  <template v-else>--</template>
                </td>
                <td>
                  <button class="btn-detail" @click="viewFundDetail(holding)">详情</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 市场热点（AI 关注分析） -->
    <div v-if="hotspots" class="card">
      <div class="card-header">
        <h3>🔥 市场热点 · AI 关注分析</h3>
        <span class="badge" :class="hotspotBadge(hotspots.overall)">{{ hotspots.overall }}</span>
      </div>
      <div class="card-body">
        <div class="hotspot-comment">
          <span class="hotspot-ai">AI 点评</span>
          <span>{{ hotspots.comment }}</span>
        </div>
        <div class="hotspot-list">
          <div v-for="(h, hi) in hotspots.hotspots" :key="hi" class="hotspot-item">
            <div class="hs-top">
              <span class="hs-theme">{{ h.theme }}</span>
              <span class="hs-score">热度 {{ h.hot_score }}</span>
            </div>
            <div class="hs-metrics">
              <span class="hs-m" :class="h.avg_day >= 0 ? 'profit' : 'loss'">日 <template v-if="h.avg_day > 0">+</template>{{ h.avg_day }}%</span>
              <span class="hs-m muted">周 <template v-if="h.avg_week > 0">+</template>{{ h.avg_week }}%</span>
              <span class="hs-m muted">月 <template v-if="h.avg_month > 0">+</template>{{ h.avg_month }}%</span>
              <span class="hs-count">{{ h.count }} 只</span>
            </div>
            <div v-if="h.related && h.related.length" class="hs-related">
              <span class="hs-rel-tag" v-for="(r, ri) in h.related" :key="ri">
                {{ r.held ? '🟢持仓' : '👀观察' }} {{ r.fund_name }}
                <span :class="r.day_return >= 0 ? 'profit' : 'loss'">{{ r.day_return >= 0 ? '+' : '' }}{{ r.day_return }}%</span>
              </span>
            </div>
            <div v-else class="hs-related muted">观察池暂无该主题基金，AI 不盲目追热点</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 双经理经营对比 -->
    <div v-if="aiCompare && aiCompare.users.length >= 2" class="card">
      <div class="card-header">
        <h3>🤝 双 AI 基金经理经营对比</h3>
        <span class="muted">稳健 vs 激进 · 同一本金 10 万起步</span>
      </div>
      <div class="card-body">
        <div class="cmp-grid">
          <div v-for="(u, ui) in aiCompare.users" :key="u.id" class="cmp-user" :class="ui === 0 ? 'cmp-a' : 'cmp-b'">
            <div class="cmp-head">
              <span class="cmp-avatar">{{ u.avatar }}</span>
              <div>
                <div class="cmp-name">{{ u.name }}</div>
                <div class="cmp-style">{{ u.style }}</div>
              </div>
              <span class="cmp-pnl" :class="u.total_return_pct >= 0 ? 'profit' : 'loss'">
                {{ u.total_return_pct >= 0 ? '+' : '' }}{{ u.total_return_pct }}%
              </span>
            </div>
            <div class="cmp-metrics">
              <div class="cmp-m"><span class="cmp-k">总资产</span><span class="cmp-v">¥{{ u.total_assets.toLocaleString() }}</span></div>
              <div class="cmp-m"><span class="cmp-k">累计收益</span><span class="cmp-v" :class="u.total_return >= 0 ? 'profit' : 'loss'">{{ u.total_return >= 0 ? '+' : '' }}¥{{ u.total_return.toLocaleString() }}</span></div>
              <div class="cmp-m"><span class="cmp-k">现金/持仓</span><span class="cmp-v">¥{{ u.cash.toLocaleString() }} / ¥{{ u.market_value.toLocaleString() }}</span></div>
              <div class="cmp-m"><span class="cmp-k">已实现盈亏</span><span class="cmp-v" :class="u.realized_pnl >= 0 ? 'profit' : 'loss'">{{ u.realized_pnl >= 0 ? '+' : '' }}¥{{ u.realized_pnl.toLocaleString() }}</span></div>
              <div class="cmp-m"><span class="cmp-k">费用合计</span><span class="cmp-v">¥{{ u.fee_stats.total_fee.toFixed(2) }}</span></div>
              <div class="cmp-m"><span class="cmp-k">交易/观察池</span><span class="cmp-v">{{ u.tx_count }} 笔 / {{ u.watchlist_count }} 只</span></div>
            </div>
          </div>
        </div>
        <div id="compareChart" class="cmp-chart"></div>
      </div>
    </div>

    <!-- AI 决策轨迹 -->
    <div v-if="aiActivity.length" class="card">
      <div class="card-header">
        <h3>🧠 AI 决策轨迹</h3>
        <span class="badge info">最近 {{ aiActivity.length }} 条动作</span>
      </div>
      <div class="card-body">
        <div class="activity-list">
          <div v-for="(act, idx) in aiActivity" :key="idx" class="activity-item">
            <span class="act-time">{{ formatDate(act.time) }}</span>
            <span class="act-type" :class="'type-' + act.type">
              {{ act.type === 'buy' ? '买入' : act.type === 'sell' ? '卖出' : act.type === 'pending' ? '待确认' : act.type === 'risk' ? '风控' : act.type === 'hotspot' ? '热点' : act.type === 'analysis' ? '分析' : '系统' }}
            </span>
            <div class="act-body">
              <div class="act-title">{{ act.title }}{{ act.fund_name && !act.title.includes(act.fund_name) ? ' · ' + act.fund_name : '' }}</div>
              <div v-if="act.desc" class="act-desc">{{ act.desc }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 待确认订单（T+1） -->
    <div v-if="pendingTxs.length" class="card">
      <div class="card-header">
        <h3>⏳ 待确认订单</h3>
        <span class="badge warning">{{ pendingTxs.length }} 笔 · T+1 确认（20:00 按官方净值落账）</span>
      </div>
      <div class="card-body">
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>下单日</th>
                <th>操作</th>
                <th>基金代码</th>
                <th>基金名称</th>
                <th>金额</th>
                <th>份额</th>
                <th>参考净值</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in pendingTxs" :key="p.id">
                <td>{{ formatDate(p.order_date) }}</td>
                <td>
                  <span :class="p.order_type === 'BUY' ? 'tag-buy' : 'tag-sell'">
                    {{ p.order_type === 'BUY' ? '买入' : '卖出' }}
                  </span>
                </td>
                <td class="code">{{ p.fund_code }}</td>
                <td class="name">{{ p.fund_name }}</td>
                <td class="number">{{ p.order_type === 'BUY' ? '¥' + p.amount.toFixed(2) : '—' }}</td>
                <td class="number">{{ p.shares ? p.shares.toLocaleString() : '—' }}</td>
                <td class="number">¥{{ p.price.toFixed(4) }}</td>
                <td><span class="tag-pending">待确认</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 交易记录 -->
    <div class="card">
      <div class="card-header">
        <h3>📝 交易记录</h3>
        <span class="badge info">{{ transactions.length }} 笔</span>
      </div>
      <div class="card-body">
        <div v-if="transactions.length === 0" class="empty-state">
          <div class="empty-icon">📝</div>
          <p>暂无交易记录</p>
        </div>
        <div v-else class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>交易时间</th>
                <th>操作</th>
                <th>基金代码</th>
                <th>基金名称</th>
                <th>金额</th>
                <th>手续费</th>
                <th>份额</th>
                <th>净值</th>
                <th>原因</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(tx, index) in transactions" :key="index">
                <td>{{ tx.date }}</td>
                <td>
                  <span :class="tx.action === '买入' ? 'tag-buy' : 'tag-sell'">
                    {{ tx.action }}
                  </span>
                </td>
                <td class="code">{{ tx.fund_code }}</td>
                <td class="name">{{ tx.fund_name }}</td>
                <td class="number">¥{{ tx.amount.toFixed(2) }}</td>
                <td class="number" :class="tx.fees > 0 ? 'fee' : ''">{{ tx.fees > 0 ? '¥' + tx.fees.toFixed(2) : '—' }}</td>
                <td class="number">{{ tx.shares.toLocaleString() }}</td>
                <td class="number">¥{{ tx.price.toFixed(4) }}</td>
                <td class="reason">{{ tx.reason }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 观察池 -->
    <div class="card">
      <div class="card-header">
        <h3>👁️ 观察池</h3>
        <div class="watch-actions">
          <span class="badge warning">{{ watchList.length }} 只</span>
          <button class="ai-discover-btn" :disabled="discovering" @click="discoverWatchlist()">
            {{ discovering ? 'AI 筛选中...' : '🔄 刷新AI推荐' }}
          </button>
        </div>
      </div>
      <div class="card-body">
        <div class="watch-grid">
          <div v-for="fund in watchList" :key="fund.code" class="watch-item" @click="viewFundDetail(fund)">
            <div class="watch-header">
              <span class="watch-code">{{ fund.code }}</span>
              <span class="watch-type">{{ fund.type }}</span>
              <span v-if="fund.source === 'ai'" class="watch-source-ai" title="由AI按当前用户性格自动筛选">AI推荐</span>
              <span v-else class="watch-source-manual" title="手动添加">手动</span>
              <button class="watch-remove" title="取消自选" @click.stop="removeWatch(fund)">✕</button>
            </div>
            <div class="watch-name">{{ fund.name }}</div>
            <div class="watch-price">
              <span class="nav">{{ fund.nav != null ? '¥' + fund.nav : '—' }}</span>
              <span v-if="fund.change != null" :class="fund.change >= 0 ? 'profit' : 'loss'">
                {{ fund.change >= 0 ? '+' : '' }}{{ fund.change }}%
              </span>
              <span v-else class="watch-date">—</span>
            </div>
            <div class="watch-date" v-if="fund.nav_date">{{ fund.nav_date }} 净值</div>
            <div class="watch-signal-row">
              <span class="watch-signal" :class="signalClass(fund.signal.action)">{{ fund.signal.label }}</span>
              <span class="watch-metrics">
                <template v-if="fund.change_5d != null">5日 {{ fund.change_5d >= 0 ? '+' : '' }}{{ fund.change_5d }}%</template>
                <template v-if="fund.change_20d != null"> · 20日 {{ fund.change_20d >= 0 ? '+' : '' }}{{ fund.change_20d }}%</template>
                <template v-if="fund.drawdown_60d != null"> · 距60日高点 {{ fund.drawdown_60d }}%</template>
                <template v-if="fund.above_ma20 != null"> · {{ fund.above_ma20 ? '站上20日线' : '20日线下' }}</template>
              </span>
            </div>
            <div class="watch-reason">{{ fund.signal.reason }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 免责声明 -->
    <div class="disclaimer">
      ⚠️ 本系统仅供学习交流，AI 操盘结果不构成任何投资建议，投资有风险。
    </div>
  </div>
    <!-- 基金详情弹窗：操作记录时间线（图标节点+增长率+悬浮明细） + 基金信息 -->
    <a-modal
      v-model:open="detailVisible"
      :footer="null"
      :width="760"
      destroy-on-close
      class="fund-detail-modal"
    >
      <template #title>
        <span v-if="detailFund">
          <span class="modal-title-name">{{ detailFund.name }}</span>
          <span class="modal-title-code">{{ detailFund.code }}</span>
        </span>
      </template>
      <a-spin :spinning="detailLoading">
        <div class="detail-modal-body">
          <div class="detail-section-title">涨幅</div>
          <div v-if="detailTxs.length === 0" class="empty-state">
            <div class="empty-icon">📝</div>
            <p>暂无该基金操作记录</p>
          </div>
          <div v-else id="detailChart" class="detail-chart"></div>

          <a-divider class="detail-divider" />

          <div class="detail-section-title">收益明细（每日盈亏）</div>
          <div class="detail-tx-table-wrap">
            <table class="detail-tx-table">
              <thead>
                <tr>
                  <th>日期</th>
                  <th>当日盈亏金额</th>
                  <th>当日涨幅</th>
                  <th>当日持有份额</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in detailDailyPnl" :key="row.date">
                  <td class="muted">{{ row.date }}</td>
                  <td :class="row.pnl >= 0 ? 'profit' : 'loss'">
                    <template v-if="row.pnl !== 0 || row.shares === 0"><template v-if="row.pnl > 0">+</template>¥{{ row.pnl.toFixed(2) }}</template>
                    <template v-else><span class="nav-date">T+1</span></template>
                  </td>
                  <td :class="(row.daily_return ?? 0) >= 0 ? 'profit' : 'loss'">
                    {{ row.daily_return >= 0 ? '+' : '' }}{{ row.daily_return.toFixed(2) }}%
                  </td>
                  <td class="number">{{ row.shares.toLocaleString() }} 份</td>
                </tr>
              </tbody>
            </table>
            <div class="tx-note">当日盈亏金额 = 当日收盘持有份额 ×（当日净值 − 前一日净值）；买入当日 T+1 无收益。今日净值公布后自动更新。</div>
          </div>

          <a-divider class="detail-divider" />

          <div class="detail-section-title">操作明细（当日涨幅 · 实际金额变动）</div>
          <div class="detail-tx-table-wrap">
            <table class="detail-tx-table">
              <thead>
                <tr>
                  <th>时间</th>
                  <th>操作</th>
                  <th>份额</th>
                  <th>净值</th>
                  <th>金额</th>
                  <th>手续费</th>
                  <th>当日涨幅</th>
                  <th>金额变动</th>
                  <th>收益</th>
                  <th>收益率</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in detailRows" :key="row.raw">
                  <td class="muted">{{ row.date }}</td>
                  <td>
                    <span class="tx-tag" :class="row.action === '买入' ? 'buy' : 'sell'">{{ row.action }}</span>
                  </td>
                  <td class="number">{{ Number(row.shares).toLocaleString() }}</td>
                  <td class="number">¥{{ Number(row.price).toFixed(4) }}</td>
                  <td class="number">¥{{ Number(row.amount).toFixed(2) }}</td>
                  <td class="number fee">¥{{ Number(row.fees || 0).toFixed(2) }}</td>
                  <td :class="(row.daily_return ?? 0) >= 0 ? 'profit' : 'loss'">
                    <template v-if="row.daily_return != null">{{ row.daily_return >= 0 ? '+' : '' }}{{ row.daily_return.toFixed(2) }}%</template>
                    <template v-else><span class="nav-date">待更新</span></template>
                  </td>
                  <td :class="row.cash_change >= 0 ? 'profit' : 'loss'">
                    {{ row.cash_change >= 0 ? '+' : '' }}¥{{ Math.abs(row.cash_change).toFixed(2) }}
                    <span class="cash-note">{{ row.action === '买入' ? '支出' : '到账' }}</span>
                  </td>
                  <td :class="row.pnl != null && row.pnl >= 0 ? 'profit' : 'loss'">
                    <template v-if="row.pnl != null">
                      <template v-if="row.pnl >= 0">+</template>¥{{ row.pnl.toFixed(2) }}
                      <span class="pnl-tag" :class="row.pnl_tag === '实' ? 'realized' : 'floating'">{{ row.pnl_tag === '实' ? '已实现' : '浮动' }}</span>
                    </template>
                    <template v-else><span class="nav-date">—</span></template>
                  </td>
                  <td :class="row.pnl_rate != null && row.pnl_rate >= 0 ? 'profit' : 'loss'">
                    <template v-if="row.pnl_rate != null"><template v-if="row.pnl_rate >= 0">+</template>{{ row.pnl_rate.toFixed(2) }}%</template>
                    <template v-else><span class="nav-date">—</span></template>
                  </td>
                </tr>
              </tbody>
            </table>
            <div class="tx-note">金额变动：买入为扣款支出（含申购费）；卖出为净到账（已扣赎回费）。当日涨幅为该操作日基金净值涨跌幅。</div>
            <div class="pnl-summary">
              <span>收益汇总：</span>
              <span :class="detailPnlSummary.realized >= 0 ? 'profit' : 'loss'">已实现 <template v-if="detailPnlSummary.realized >= 0">+</template>¥{{ detailPnlSummary.realized.toFixed(2) }}</span>
              <span class="sum-sep">·</span>
              <span :class="detailPnlSummary.floating >= 0 ? 'profit' : 'loss'">持有浮动 <template v-if="detailPnlSummary.floating >= 0">+</template>¥{{ detailPnlSummary.floating.toFixed(2) }}</span>
              <span class="sum-sep">·</span>
              <span :class="detailPnlSummary.total >= 0 ? 'profit' : 'loss'" class="sum-total">该基金合计 <template v-if="detailPnlSummary.total >= 0">+</template>¥{{ detailPnlSummary.total.toFixed(2) }}</span>
            </div>
          </div>

          <a-divider class="detail-divider" />

          <div class="detail-section-title">基金信息</div>
          <div class="detail-info-grid" v-if="detailFund">
            <div class="detail-info-item">
              <span class="label">基金代码</span>
              <span class="value">{{ detailFund.code }}</span>
            </div>
            <div class="detail-info-item">
              <span class="label">基金类型</span>
              <span class="value">{{ detailFund.type || '—' }}</span>
            </div>
            <div class="detail-info-item">
              <span class="label">基金经理</span>
              <span class="value">{{ detailFund.manager || '—' }}</span>
            </div>
            <div class="detail-info-item">
              <span class="label">成立日期</span>
              <span class="value">{{ detailFund.inception_date || '—' }}</span>
            </div>
            <div class="detail-info-item benchmark-item">
              <span class="label">业绩基准</span>
              <span class="value benchmark">{{ detailFund.benchmark || '—' }}</span>
            </div>
          </div>

          <div v-if="detailFees" class="detail-section-title" style="margin-top:18px">费率详情（真实费率）</div>
          <div v-if="detailFees" class="fee-grid">
            <div class="fee-item"><span class="fee-label">申购费率</span><span class="fee-value">{{ detailFees.buy_fee_pct }}%</span></div>
            <div class="fee-item"><span class="fee-label">管理费率（年）</span><span class="fee-value">{{ detailFees.manage_fee_pct }}%</span></div>
            <div class="fee-item"><span class="fee-label">托管费率（年）</span><span class="fee-value">{{ detailFees.custody_fee_pct }}%</span></div>
            <div class="fee-item"><span class="fee-label">销售服务费（年）</span><span class="fee-value">{{ detailFees.service_fee_pct }}%</span></div>
            <div class="fee-item fee-wide"><span class="fee-label">赎回费率（持有天数阶梯）</span>
              <span class="fee-value">
                <span v-for="(sc, si) in detailFees.sell_schedule" :key="si" class="fee-step">
                  {{ sc.days === 0 ? '≥1年' : '<' + sc.days + '天' }}：{{ sc.rate_pct }}%
                </span>
              </span>
            </div>
          </div>
        </div>
      </a-spin>
    </a-modal>
  </a-spin>
</template>

<style scoped>
/* 收益构成条 */
.ai-score-card { margin: 14px 0 4px; padding: 16px 20px; background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(139,92,246,0.08)); border: 1px solid rgba(99,102,241,0.25); border-radius: 12px; }
.score-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.score-title { font-size: 15px; font-weight: 600; color: #e2e8f0; }
.score-sub { font-size: 12px; color: #64748b; }
.score-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.score-item { padding: 10px 12px; background: rgba(15,20,40,0.5); border-radius: 8px; }
.s-label { font-size: 12px; color: #94a3b8; margin-bottom: 4px; }
.s-value { font-size: 14px; font-weight: 600; color: #e2e8f0; }
.s-value small { font-weight: 400; color: #64748b; font-size: 11px; }
.risk-tag { display: inline-block; margin-right: 6px; padding: 1px 8px; border-radius: 8px; font-size: 11px; background: rgba(139,92,246,0.15); color: #a78bfa; }
.activity-list { display: flex; flex-direction: column; gap: 8px; }
.activity-item { display: flex; align-items: flex-start; gap: 12px; padding: 10px 12px; background: rgba(15,20,40,0.4); border-radius: 8px; }
.act-time { font-size: 12px; color: #64748b; white-space: nowrap; padding-top: 2px; }
.act-type { flex: 0 0 auto; padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.type-buy { background: rgba(16,185,129,0.15); color: #34d399; }
.type-sell { background: rgba(244,63,94,0.15); color: #f87171; }
.type-pending { background: rgba(245,158,11,0.15); color: #f59e0b; }
.type-risk { background: rgba(244,63,94,0.15); color: #fb7185; }
.type-analysis { background: rgba(99,102,241,0.15); color: #818cf8; }
.type-audit { background: rgba(148,163,184,0.15); color: #94a3b8; }
.type-hotspot { background: rgba(251,191,36,0.15); color: #fbbf24; }
.hotspot-comment { display: flex; gap: 10px; align-items: flex-start; padding: 10px 14px; background: rgba(251,191,36,0.06); border: 1px solid rgba(251,191,36,0.18); border-radius: 10px; font-size: 13px; color: #cbd5e1; line-height: 1.6; margin-bottom: 12px; }
.hotspot-ai { flex: 0 0 auto; padding: 1px 10px; border-radius: 10px; background: rgba(251,191,36,0.15); color: #fbbf24; font-size: 12px; font-weight: 600; }
.hotspot-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 10px; }
.hotspot-item { padding: 12px 14px; background: rgba(15,20,40,0.4); border-radius: 10px; }
.hs-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.hs-theme { font-size: 14px; font-weight: 600; color: #e2e8f0; }
.hs-score { font-size: 11px; color: #fbbf24; background: rgba(251,191,36,0.1); padding: 1px 8px; border-radius: 8px; }
.hs-metrics { display: flex; gap: 10px; font-size: 12px; margin-bottom: 8px; }
.hs-m { color: #cbd5e1; }
.hs-count { margin-left: auto; color: #64748b; font-size: 11px; }
.hs-related { display: flex; flex-wrap: wrap; gap: 6px; font-size: 12px; }
.hs-rel-tag { padding: 2px 8px; border-radius: 8px; background: rgba(99,102,241,0.1); color: #a5b4fc; }
.badge.hotspot-hot { background: rgba(244,63,94,0.2); color: #fb7185; }
.badge.hotspot-warm { background: rgba(251,191,36,0.2); color: #fbbf24; }
.badge.hotspot-mild { background: rgba(52,211,153,0.15); color: #34d399; }
.badge.hotspot-cold { background: rgba(100,116,139,0.2); color: #94a3b8; }
.cmp-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; margin-bottom: 14px; }
.cmp-user { padding: 14px; border-radius: 12px; }
.cmp-a { background: rgba(52,211,153,0.06); border: 1px solid rgba(52,211,153,0.22); }
.cmp-b { background: rgba(251,191,36,0.06); border: 1px solid rgba(251,191,36,0.22); }
.cmp-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.cmp-avatar { font-size: 22px; }
.cmp-name { font-size: 15px; font-weight: 600; color: #e2e8f0; }
.cmp-style { font-size: 11px; color: #94a3b8; }
.cmp-pnl { margin-left: auto; font-size: 16px; font-weight: 700; }
.cmp-metrics { display: flex; flex-direction: column; gap: 6px; }
.cmp-m { display: flex; justify-content: space-between; font-size: 12px; }
.cmp-k { color: #94a3b8; }
.cmp-v { color: #cbd5e1; font-weight: 600; }
.cmp-chart { width: 100%; height: 240px; }
.muted { color: #64748b; font-size: 12px; font-weight: 400; }
.type-order { background: rgba(6,182,212,0.15); color: #22d3ee; }
.act-body { flex: 1; min-width: 0; }
.act-title { font-size: 13px; color: #cbd5e1; }
.act-desc { font-size: 12px; color: #64748b; margin-top: 2px; line-height: 1.5; }
.fee-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 10px; }
.fee-item { padding: 8px 12px; background: rgba(15,20,40,0.4); border-radius: 8px; }
.fee-wide { grid-column: 1 / -1; }
.fee-label { font-size: 12px; color: #94a3b8; display: block; margin-bottom: 4px; }
.fee-value { font-size: 13px; color: #e2e8f0; font-weight: 600; }
.fee-wide .fee-value { display: flex; flex-wrap: wrap; gap: 6px; }
.fee-step { display: inline-block; padding: 1px 8px; border-radius: 8px; background: rgba(99,102,241,0.12); color: #a5b4fc; font-size: 12px; }
.pnl-breakdown { display: flex; flex-wrap: wrap; gap: 12px; margin: 14px 0 4px; }
.bd-item { display: flex; align-items: center; gap: 10px; padding: 10px 18px; background: var(--card-bg, #1c2348); border: 1px solid rgba(99,102,241,0.15); border-radius: 10px; font-size: 13px; }
.bd-item .bd-label { color: #94a3b8; }
.bd-item.bd-total { background: linear-gradient(135deg, rgba(99,102,241,0.18), rgba(139,92,246,0.12)); border-color: rgba(99,102,241,0.35); }
.profit { color: #34d399; }
.loss { color: #f87171; }
.nav-date { color: #64748b; font-size: 12px; }
.tag-pending { display: inline-block; padding: 2px 10px; border-radius: 10px; font-size: 12px; background: rgba(245,158,11,0.15); color: #f59e0b; }

.dashboard {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

/* 用户信息栏 */
.user-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: linear-gradient(135deg, #171b44 0%, #2a2f7a 60%, #3b3fc0 100%);
  border-radius: 16px;
  color: white;
  margin-bottom: 16px;
}

.user-bar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-bar-avatar { font-size: 36px; }

.user-bar-info { display: flex; flex-direction: column; }

.user-bar-name { font-size: 18px; font-weight: 600; }

.user-bar-desc { font-size: 13px; color: var(--text-muted); margin-top: 4px; }

.user-bar-right { display: flex; gap: 24px; }

.user-bar-stat { display: flex; flex-direction: column; align-items: center; }

.stat-label { font-size: 12px; color: var(--text-muted); }

.stat-value { font-size: 18px; font-weight: 600; color: #60a5fa; }

/* 状态栏 */
.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%);
  border-radius: 16px;
  color: white;
  margin-bottom: 16px;
}

.status-left { display: flex; align-items: center; gap: 12px; }

.status-dot {
  width: 10px;
  height: 10px;
  background: #34d399;
  border-radius: 50%;
  animation: puise 2s infinite;
}

.status-dot.analyzing {
  background: #f59e0b;
  animation: puise-fast 0.5s infinite;
}

@keyframes puise {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.1); }
}

@keyframes puise-fast {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
}

.status-text { font-weight: 600; font-size: 16px; }

.status-divider { opacity: 0.5; }

.status-info { font-size: 14px; opacity: 0.9; }

.status-right { display: flex; align-items: center; gap: 12px; }

.next-analysis {
  font-size: 14px;
  opacity: 0.9;
  background: rgba(255, 255, 255, 0.15);
  padding: 6px 12px;
  border-radius: 20px;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover:not(.disabled) {
  background: rgba(255, 255, 255, 0.3);
}

.refresh-btn.disabled { opacity: 0.6; cursor: not-allowed; }

.refresh-icon { font-size: 16px; display: inline-block; }

.refresh-icon.spinning { animation: spin 1s linear infinite; }

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 分析进度条 */
.analysis-progress-bar {
  margin-bottom: 16px;
  padding: 12px 20px;
  background: var(--card);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.progress-bar {
  height: 8px;
  background: #262c56;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text { font-size: 13px; color: var(--text-secondary); text-align: center; }

/* 资产总览卡片 */
.overview-cards {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.overview-card {
  background: var(--card);
  border-radius: 16px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow, 0 1px 3px rgba(15, 23, 42, 0.06), 0 8px 24px rgba(15, 23, 42, 0.04));
  border: 1px solid var(--border, #eef0f5);
  transition: all 0.3s;
}

.overview-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-hover, 0 12px 32px rgba(15, 23, 42, 0.1));
}

.overview-card.primary { border-left: 4px solid #6366f1; }
.overview-card.success { border-left: 4px solid #10b981; }
.overview-card.danger { border-left: 4px solid #ef4444; }
.overview-card.info { border-left: 4px solid #06b6d4; }
.overview-card.warning { border-left: 4px solid #f59e0b; }

.card-icon { font-size: 28px; }

.card-content { flex: 1; }

.card-label { font-size: 13px; color: var(--text-secondary); margin-bottom: 4px; }

.card-value { font-size: 20px; font-weight: 700; color: var(--text); }

/* 图表区域 */
.charts-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.chart-card {
  background: var(--card);
  border-radius: 16px;
  padding: 24px;
  box-shadow: var(--shadow, 0 1px 3px rgba(15, 23, 42, 0.06), 0 8px 24px rgba(15, 23, 42, 0.04));
  border: 1px solid var(--border, #eef0f5);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-header h3 { font-size: 16px; font-weight: 600; color: var(--text); margin: 0; }

.chart-tabs { display: flex; gap: 8px; }

.tab {
  padding: 6px 12px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 8px;
}

.tab.active { background: #6366f1; color: white; }

.chart-container { height: 250px; }

.chart-empty {
  height: 100%;
  min-height: 250px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  text-align: center;
  gap: 6px;
}

.chart-empty .empty-icon { font-size: 32px; }

.chart-empty p { font-size: 13px; margin: 0; }

.chart-empty .chart-empty-sub { font-size: 12px; color: var(--text-secondary); }

/* 卡片 */
.card {
  background: var(--card);
  border-radius: 16px;
  box-shadow: var(--shadow, 0 1px 3px rgba(15, 23, 42, 0.06), 0 8px 24px rgba(15, 23, 42, 0.04));
  border: 1px solid var(--border, #eef0f5);
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border, #eef0f5);
}

.card-header h3 { font-size: 16px; font-weight: 600; color: var(--text); margin: 0; }

.card-body { padding: 20px 24px; }

.badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.badge.success { background: rgba(52, 211, 153, 0.12); color: #34d399; }
.badge.info { background: rgba(56, 189, 248, 0.12); color: #38bdf8; }
.badge.warning { background: rgba(251, 191, 36, 0.12); color: #fbbf24; }

/* 表格 */
.table-container { overflow-x: auto; }

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.data-table th {
  background: var(--bg-soft);
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: var(--text-secondary);
  border-bottom: 2px solid var(--border-strong);
}

.data-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}

.data-table tr:hover { background: var(--bg-soft); }

.data-table .code { font-family: 'SF Mono', monospace; color: #6366f1; }

.data-table .name { font-weight: 500; color: var(--text); }

.data-table .number { text-align: right; font-family: 'SF Mono', monospace; }

.data-table .reason { color: var(--text-secondary); max-width: 200px; }

.profit { color: #10b981; font-weight: 600; }
.loss { color: #ef4444; font-weight: 600; }

.est-time {
  margin-left: 4px;
  cursor: help;
}

.t1-tag {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 6px;
  font-size: 11px;
  font-weight: 500;
  color: #a78bfa;
  background: rgba(139, 92, 246, 0.18);
  border-radius: 4px;
  vertical-align: 1px;
  cursor: help;
}

.tag-buy {
  display: inline-block;
  padding: 4px 8px;
  background: rgba(52, 211, 153, 0.14);
  color: #34d399;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.tag-sell {
  display: inline-block;
  padding: 4px 8px;
  background: rgba(248, 113, 113, 0.14);
  color: #f87171;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.btn-detail {
  padding: 6px 12px;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-detail:hover { background: #4f46e5; }

/* 观察池 */
.watch-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ai-discover-btn {
  padding: 5px 12px;
  border: none;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  cursor: pointer;
  transition: opacity 0.2s;
}

.ai-discover-btn:hover { opacity: 0.88; }
.ai-discover-btn:disabled { opacity: 0.55; cursor: not-allowed; }

.watch-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
}

.watch-item {
  padding: 16px;
  background: var(--bg-soft);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.watch-item:hover {
  border-color: rgba(129, 140, 248, 0.6);
  box-shadow: var(--shadow-hover);
}

.watch-header { display: flex; justify-content: space-between; margin-bottom: 8px; }

.watch-source-ai,
.watch-source-manual {
  font-size: 11px;
  padding: 1px 7px;
  border-radius: 6px;
  font-weight: 600;
  margin-left: 6px;
  white-space: nowrap;
}

.watch-source-ai {
  color: #c4b5fd;
  background: rgba(139, 92, 246, 0.2);
}

.watch-source-manual {
  color: #a5abcf;
  background: rgba(148, 163, 184, 0.14);
}

.watch-remove {
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 12px;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
  border-radius: 4px;
}

.watch-remove:hover {
  color: #f87171;
  background: rgba(248, 113, 113, 0.15);
}

.watch-code {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  color: #a5b4fc;
  background: rgba(99, 102, 241, 0.15);
  padding: 2px 8px;
  border-radius: 4px;
}

.watch-type { font-size: 12px; color: var(--text-secondary); }

.watch-name { font-weight: 600; color: var(--text); margin-bottom: 8px; }

.watch-price { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }

.watch-price .nav { font-weight: 600; font-size: 16px; }

.watch-date { font-size: 12px; color: var(--text-muted); margin-bottom: 4px; }

.watch-signal-row { margin-bottom: 6px; }

.watch-signal {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  margin-right: 6px;
}

.signal-buy { color: #34d399; background: rgba(52, 211, 153, 0.15); }
.signal-add { color: #fbbf24; background: rgba(251, 191, 36, 0.15); }
.signal-watch { color: #60a5fa; background: rgba(59, 130, 246, 0.15); }
.signal-wait { color: var(--text-secondary); background: rgba(148, 163, 184, 0.12); }

.watch-metrics { font-size: 12px; color: var(--text-secondary); }

.watch-reason { font-size: 12px; color: var(--text-secondary); line-height: 1.5; }

.empty-state { text-align: center; padding: 40px 20px; color: var(--text-secondary); }

.empty-icon { font-size: 48px; margin-bottom: 12px; }

.disclaimer {
  text-align: center;
  padding: 16px;
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--card);
  border-radius: 12px;
  border: 1px solid var(--border);
}

/* 响应式 */
@media (max-width: 1200px) {
  .overview-cards { grid-template-columns: repeat(3, 1fr); }
  .charts-section { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .dashboard { padding: 16px; }
  .overview-cards { grid-template-columns: repeat(2, 1fr); }
  .watch-grid { grid-template-columns: 1fr; }
  .status-bar { flex-direction: column; gap: 12px; }
}
.nav-date {
  font-size: 11px;
  color: rgba(148, 163, 184, 0.7);
  margin-left: 2px;
}
.t1-tag {
  display: inline-block;
  margin-left: 4px;
  padding: 0 4px;
  font-size: 10px;
  line-height: 16px;
  border-radius: 3px;
  background: rgba(99, 102, 241, 0.15);
  color: #a5b4fc;
  cursor: help;
}
.detail-tx-table-wrap { margin-top: 4px; overflow-x: auto; }
.detail-tx-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.detail-tx-table th { text-align: left; padding: 8px 10px; color: var(--text-muted); font-weight: 500; border-bottom: 1px solid var(--border); white-space: nowrap; }
.detail-tx-table td { padding: 8px 10px; color: var(--text); border-bottom: 1px solid rgba(255,255,255,0.04); white-space: nowrap; }
.detail-tx-table .number { font-variant-numeric: tabular-nums; }
.detail-tx-table .fee { color: #fbbf24; }
.tx-tag { display: inline-block; padding: 1px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; }
.tx-tag.buy { background: rgba(52,211,153,0.15); color: #34d399; }
.tx-tag.sell { background: rgba(248,113,113,0.15); color: #f87171; }
.cash-note { font-size: 11px; color: var(--text-muted); margin-left: 4px; }
.tx-note { margin-top: 8px; font-size: 12px; color: var(--text-muted); line-height: 1.6; }
.pnl-tag { font-size: 11px; margin-left: 4px; padding: 0 4px; border-radius: 4px; }
.pnl-tag.realized { background: rgba(129,140,248,0.15); color: #818cf8; }
.pnl-tag.floating { background: rgba(52,211,153,0.12); color: #34d399; }
.pnl-summary { margin-top: 10px; padding: 10px 14px; background: rgba(99,102,241,0.07); border-radius: 10px; font-size: 13px; display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.pnl-summary .sum-sep { color: var(--text-muted); }
.pnl-summary .sum-total { font-weight: 700; }
.detail-tx-table .profit { color: #34d399; }
.detail-tx-table .loss { color: #f87171; }

/* 基金详情弹窗 */
.fund-detail-modal :deep(.ant-modal-content) {
  background: #1c2348;
  border: 1px solid #2c3466;
  border-radius: 16px;
}
.fund-detail-modal :deep(.ant-modal-header) {
  background: transparent;
  border-bottom: 1px solid #2c3466;
  padding-bottom: 14px;
}
.fund-detail-modal :deep(.ant-modal-title) {
  color: var(--text);
  font-weight: 600;
}
.modal-title-name { color: var(--text); }
.modal-title-code { color: var(--text-muted); font-size: 13px; margin-left: 8px; }
.detail-modal-body { padding: 4px 6px; }
.detail-section-title {
  color: var(--text);
  font-weight: 600;
  margin-bottom: 14px;
}
.detail-timeline {
  max-height: 320px;
  overflow-y: auto;
  padding: 4px 6px;
}
.detail-chart {
  height: 280px;
  width: 100%;
  margin: 4px 0 8px;
}

.detail-timeline :deep(.ant-timeline-item-tail) {
  border-left: 2px solid #2c3466;
}
.tx-node {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 2px 0 12px;
  cursor: default;
}
.tx-growth {
  font-size: 12px;
  font-weight: 600;
  line-height: 1.2;
}
.tx-growth.profit { color: #34d399; }
.tx-growth.loss { color: #f87171; }
.tx-main {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.tx-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 6px;
  font-size: 11px;
  color: #fff;
}
.tx-icon.icon-buy { background: rgba(52, 211, 153, 0.2); color: #34d399; }
.tx-icon.icon-sell { background: rgba(248, 113, 113, 0.2); color: #f87171; }
.tx-date { color: var(--text-muted); font-size: 13px; }
.tx-action { font-size: 12px; padding: 1px 8px; border-radius: 4px; font-weight: 500; }
.tx-action.tag-buy { background: rgba(52, 211, 153, 0.15); color: #34d399; }
.tx-action.tag-sell { background: rgba(248, 113, 113, 0.15); color: #f87171; }
.tx-amount { color: var(--text); font-weight: 600; font-size: 14px; }
.tx-fee { color: var(--text-muted); font-size: 12px; }
.detail-divider {
  border-color: #2c3466;
  margin: 4px 0 16px;
}
.detail-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 24px;
}
.detail-info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}
.detail-info-item .label { color: var(--text-muted); font-size: 13px; flex-shrink: 0; }
.detail-info-item .value { color: var(--text); font-weight: 500; text-align: right; }
.detail-info-item .benchmark { font-size: 12px; line-height: 1.5; }
.benchmark-item { grid-column: 1 / -1; }

</style>