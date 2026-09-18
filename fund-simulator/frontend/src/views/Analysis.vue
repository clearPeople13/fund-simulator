<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  ThunderboltOutlined,
  WalletOutlined,
  LineChartOutlined,
  DollarOutlined,
  DashboardOutlined,
  ArrowDownOutlined,
  LineOutlined,
  BarChartOutlined,
  InfoCircleFilled,
  CheckCircleFilled,
  WarningFilled
, TagsOutlined } from '@ant-design/icons-vue'
import axios from 'axios'
import * as echarts from 'echarts'

const router = useRouter()
const loading = ref(true)
const activeTab = ref('performance')

// 真实数据状态
const portfolioStats = ref({
  initial_capital: 100000,
  current_assets: 100000,
  totalReturn: 0,
  totalReturnRate: 0,
  tradingCount: 0
})
const feeStats = ref({ buy_fee: 0, sell_fee: 0, total_fee: 0 })
const performance = ref({
  totalReturn: 0,
  totalReturnRate: 0,
  annualizedReturn: null,
  benchmarkReturn: null,
  alpha: null,
  beta: null
})
const risk = ref({ volatility: null, maxDrawdown: null, sharpeRatio: null, sortinoRatio: null })
const holdings = ref([])
const tradingStats = ref({ total: 0, buys: 0, sells: 0, winRate: null, profitLossRatio: null, avgHoldDays: null })
const dailyHistory = ref([])
const runDays = ref(1)
const palette = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#06b6d4', '#10b981', '#f59e0b', '#3b82f6']

// a-table 列配置（持仓明细）
const holdingColumns = [
  { title: '基金代码', dataIndex: 'code', key: 'code', width: 100 },
  { title: '基金名称', dataIndex: 'name', key: 'name', ellipsis: true },
  { title: '配置比例', key: 'allocation', width: 120, align: 'center' },
  { title: '近6月收益', key: 'recent_return', width: 110, align: 'right' }
]

// 初始化收益曲线图（真实每日快照）
const initPerformanceChart = () => {
  const chartDom = document.getElementById('performanceChart')
  if (!chartDom) return
  const existingChart = echarts.getInstanceByDom(chartDom)
  if (existingChart) existingChart.dispose()

  const data = dailyHistory.value
  if (data.length < 2) {
    chartDom.innerHTML = `<div style="height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#94a3b8;font-size:14px;gap:8px">
      <div style="font-size:36px">📈</div>
      <div>系统自 ${data[0]?.date || '今日'} 开始记录，暂无收益曲线历史</div>
      <div style="font-size:12px;color:#cbd5e1">运行第 ${runDays.value} 天，每日收盘后自动积累</div>
    </div>`
    return
  }

  const dates = data.map(d => d.date.slice(5).replace('-', '/'))
  const portfolioData = data.map(d => Math.round(d.total_assets))
  const myChart = echarts.init(chartDom)

  const option = {
    title: { text: '', left: 'center' },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(30,41,59,0.9)',
      borderWidth: 0,
      textStyle: { color: '#f8fafc' },
      formatter: function (params) {
        const p = params[0]
        return `${p.axisValue}<br/><span style="color:#a5b4fc">${p.seriesName}</span>: ¥${p.value.toLocaleString()}`
      }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLine: { lineStyle: { color: '#2c3466' } },
      axisLabel: { color: '#8b92b8', rotate: 45, interval: 29 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: '¥{value}', color: '#8b92b8' },
      splitLine: { lineStyle: { color: '#2e3768' } }
    },
    series: [{
      name: '我的组合',
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      showSymbol: false,
      lineStyle: { color: '#6366f1', width: 3 },
      itemStyle: { color: '#6366f1' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(99, 102, 241, 0.35)' },
          { offset: 1, color: 'rgba(99, 102, 241, 0.02)' }
        ])
      },
      data: portfolioData
    }]
  }
  myChart.setOption(option)
}

// 初始化资产配置图（真实持仓市值占比）
const initAllocationChart = () => {
  const chartDom = document.getElementById('allocationChart')
  if (!chartDom) return
  const existingChart = echarts.getInstanceByDom(chartDom)
  if (existingChart) existingChart.dispose()

  if (holdings.value.length === 0) {
    chartDom.innerHTML = '<div style="height:100%;display:flex;align-items:center;justify-content:center;color:#94a3b8;font-size:14px">暂无持仓</div>'
    return
  }

  const myChart = echarts.init(chartDom)
  const option = {
    tooltip: { trigger: 'item', backgroundColor: 'rgba(30,41,59,0.9)', borderWidth: 0, textStyle: { color: '#f8fafc' }, formatter: '{b}<br/>占比: {d}%' },
    legend: { bottom: 0, icon: 'circle', itemWidth: 8, itemHeight: 8, textStyle: { color: '#8b92b8', fontSize: 12 } },
    series: [{
      name: '资产配置',
      type: 'pie',
      radius: ['42%', '68%'],
      center: ['50%', '46%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 8, borderColor: '#1c2348', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold', formatter: '{b}\n{d}%' } },
      data: holdings.value.map((item, index) => ({
        value: item.allocation,
        name: item.name,
        itemStyle: { color: palette[index % palette.length] }
      }))
    }]
  }
  myChart.setOption(option)
}

// 加载真实数据
const loadData = async () => {
  try {
    loading.value = true
    const [pfRes, fundsRes, txRes, dailyRes] = await Promise.all([
      axios.get('/api/ai/portfolio'),
      axios.get('/api/funds', { params: { limit: 100 } }),
      axios.get('/api/ai/transactions'),
      axios.get('/api/ai/daily')
    ])
    const pf = pfRes.data || {}
    const funds = (fundsRes.data && fundsRes.data.data) || []
    const txs = Array.isArray(txRes.data) ? txRes.data : []
    const daily = Array.isArray(dailyRes.data) ? dailyRes.data : []
    dailyHistory.value = daily
    runDays.value = Math.max(1, daily.length)

    const fundMap = {}
    funds.forEach(f => { fundMap[f.fund_code] = f })

    // 持仓与配置比例（按最新市值）
    const rows = []
    const mvs = {}
    let totalMv = 0
    for (const [code, h] of Object.entries(pf.holdings || {})) {
      const fund = fundMap[code] || {}
      // 市值优先用后端持仓 market_value（fund_nav 最新净值口径）；fundMap 仅 universe top100，持仓基金可能不在其中
      mvs[code] = h.market_value != null ? h.market_value : (h.shares * (fund.latest_nav != null ? fund.latest_nav : h.cost))
      totalMv += mvs[code]
    }
    for (const [code, h] of Object.entries(pf.holdings || {})) {
      const fund = fundMap[code] || {}
      rows.push({
        code,
        name: fund.fund_name || code,
        allocation: totalMv > 0 ? Number((mvs[code] / totalMv * 100).toFixed(1)) : 0,
        recent_return: fund.recent_return
      })
    }
    holdings.value = rows

    // 收益指标（真实）
    const currentAssets = (pf.current_capital || 0) + totalMv
    const initial = pf.initial_capital || 100000
    const totalReturn = currentAssets - initial
    const totalReturnRate = initial > 0 ? Number((totalReturn / initial * 100).toFixed(2)) : 0
    performance.value = {
      totalReturn,
      totalReturnRate,
      annualizedReturn: null,
      benchmarkReturn: null,
      alpha: null,
      beta: null
    }
    portfolioStats.value = {
      initial_capital: initial,
      current_assets: currentAssets,
      totalReturn,
      totalReturnRate,
      tradingCount: txs.length
    }
    feeStats.value = {
      buy_fee: Number(pf.fee_stats?.buy_fee || 0),
      sell_fee: Number(pf.fee_stats?.sell_fee || 0),
      total_fee: Number(pf.fee_stats?.total_fee || 0)
    }

    // 交易统计（真实）
    tradingStats.value = {
      total: txs.length,
      buys: txs.filter(t => t.transaction_type === 'BUY').length,
      sells: txs.filter(t => t.transaction_type === 'SELL').length,
      winRate: null,
      profitLossRatio: null,
      avgHoldDays: null
    }

    loading.value = false
    setTimeout(() => {
      initPerformanceChart()
      initAllocationChart()
    }, 100)
  } catch (error) {
    console.error('加载数据失败:', error)
    loading.value = false
  }
}

// 跳转到AI分析
const goToAIAnalysis = () => {
  router.push('/ai-analysis')
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <a-spin :spinning="loading">
  <div class="analysis-container">
    <!-- Hero 头图 -->
    <div class="hero">
      <div class="hero-content">
        <div class="hero-left">
          <div class="hero-tag">AI 投资分析</div>
          <h1>投资分析</h1>
          <p>全面分析你的投资组合表现、风险指标和资产配置</p>
        </div>
        <div class="hero-right">
          <button class="hero-btn" @click="goToAIAnalysis">
            <ThunderboltOutlined />
            AI智能分析
          </button>
        </div>
      </div>
    </div>

    <!-- 概览统计 -->
    <div class="stats-grid">
      <div class="stat-card stat-indigo">
        <div class="stat-icon"><WalletOutlined /></div>
        <div class="stat-body">
          <div class="stat-label">初始资金</div>
          <div class="stat-value">¥{{ portfolioStats.initial_capital.toLocaleString() }}</div>
        </div>
      </div>
      <div class="stat-card stat-violet">
        <div class="stat-icon"><LineChartOutlined /></div>
        <div class="stat-body">
          <div class="stat-label">当前资产</div>
          <div class="stat-value">¥{{ portfolioStats.current_assets.toLocaleString() }}</div>
        </div>
      </div>
      <div class="stat-card" :class="portfolioStats.totalReturn >= 0 ? 'stat-green' : 'stat-red'">
        <div class="stat-icon"><DollarOutlined /></div>
        <div class="stat-body">
          <div class="stat-label">累计收益</div>
          <div class="stat-value">{{ portfolioStats.totalReturn >= 0 ? '+' : '' }}¥{{ portfolioStats.totalReturn.toLocaleString() }}</div>
        </div>
      </div>
      <div class="stat-card" :class="portfolioStats.totalReturnRate >= 0 ? 'stat-green' : 'stat-red'">
        <div class="stat-icon"><DashboardOutlined /></div>
        <div class="stat-body">
          <div class="stat-label">收益率</div>
          <div class="stat-value">{{ portfolioStats.totalReturnRate >= 0 ? '+' : '' }}{{ portfolioStats.totalReturnRate }}%</div>
        </div>
      </div>
      <div class="stat-card stat-gold">
        <div class="stat-icon"><TagsOutlined /></div>
        <div class="stat-body">
          <div class="stat-label">累计费用</div>
          <div class="stat-value">¥{{ feeStats.total_fee.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</div>
        </div>
      </div>
    </div>

    <!-- 分析标签页 -->
    <div class="analysis-panel">
      <div class="panel-header">
        <div class="panel-tabs">
          <button
            type="button"
            v-for="t in [
              { key: 'performance', label: '📊 收益分析' },
              { key: 'risk', label: '🛡️ 风险分析' },
              { key: 'allocation', label: '🍩 资产配置' },
              { key: 'trading', label: '💼 交易统计' }
            ]"
            :key="t.key"
            class="panel-tab"
            :class="{ active: activeTab === t.key }"
            @click="activeTab = t.key"
          >{{ t.label }}</button>
        </div>
      </div>

      <!-- 收益分析 -->
      <div v-show="activeTab === 'performance'" class="tab-content">
        <a-row :gutter="20">
          <a-col :xs="24" :md="16">
            <div class="chart-card">
              <div class="chart-card-header">
                <span class="chart-title">收益曲线</span>
                <span class="chart-sub">每日收盘后自动更新</span>
              </div>
              <div id="performanceChart" class="chart-container"></div>
            </div>
          </a-col>
          <a-col :xs="24" :md="8">
            <div class="metrics-card">
              <div class="metrics-card-header">收益指标</div>
              <div class="metric-item">
                <span class="label">累计收益</span>
                <span class="value" :class="performance.totalReturn >= 0 ? 'profit' : 'loss'">
                  {{ performance.totalReturn >= 0 ? '+' : '' }}¥{{ performance.totalReturn.toLocaleString() }}
                </span>
              </div>
              <div class="metric-item">
                <span class="label">累计收益率</span>
                <span class="value" :class="performance.totalReturnRate >= 0 ? 'profit' : 'loss'">
                  {{ performance.totalReturnRate >= 0 ? '+' : '' }}{{ performance.totalReturnRate }}%
                </span>
              </div>
              <div class="metric-item">
                <span class="label">年化收益率</span>
                <span class="value muted">— 数据不足</span>
              </div>
              <div class="metric-item">
                <span class="label">基准收益率</span>
                <span class="value muted">— 无基准数据</span>
              </div>
              <div class="metric-item">
                <span class="label">超额收益 Alpha</span>
                <span class="value muted">— 数据不足</span>
              </div>
              <div class="metric-item">
                <span class="label">系统风险 Beta</span>
                <span class="value muted">— 数据不足</span>
              </div>
              <div class="metric-item">
                <span class="label">累计费用（含买卖手续费）</span>
                <span class="value">¥{{ feeStats.total_fee.toFixed(2) }}</span>
              </div>
              <div class="metric-item">
                <span class="label">· 申购费 / 赎回费</span>
                <span class="value muted">¥{{ feeStats.buy_fee.toFixed(2) }} / ¥{{ feeStats.sell_fee.toFixed(2) }}</span>
              </div>
              <div class="metrics-note">年化/Alpha/Beta 需累计更多交易日数据后自动计算</div>
            </div>
          </a-col>
        </a-row>
      </div>

      <!-- 风险分析 -->
      <div v-show="activeTab === 'risk'" class="tab-content">
        <a-row :gutter="20">
          <a-col :xs="24" :md="12">
            <div class="metrics-card">
              <div class="metrics-card-header">风险指标</div>
              <a-alert type="info" :closable="false" show-icon style="margin-bottom: 16px; border-radius: 10px"
                :message="`当前运行第 ${runDays} 天，风险指标需累计更多交易日数据后自动计算`" />
              <div class="metric-grid">
                <div class="metric-card">
                  <div class="metric-icon volatility"><LineChartOutlined /></div>
                  <div class="metric-info">
                    <div class="metric-label">年化波动率</div>
                    <div class="metric-value">—</div>
                  </div>
                </div>
                <div class="metric-card">
                  <div class="metric-icon drawdown"><ArrowDownOutlined /></div>
                  <div class="metric-info">
                    <div class="metric-label">最大回撤</div>
                    <div class="metric-value loss">—</div>
                  </div>
                </div>
                <div class="metric-card">
                  <div class="metric-icon sharpe"><LineOutlined /></div>
                  <div class="metric-info">
                    <div class="metric-label">夏普比率</div>
                    <div class="metric-value">—</div>
                  </div>
                </div>
                <div class="metric-card">
                  <div class="metric-icon sortino"><BarChartOutlined /></div>
                  <div class="metric-info">
                    <div class="metric-label">索提诺比率</div>
                    <div class="metric-value">—</div>
                  </div>
                </div>
              </div>
            </div>
          </a-col>
          <a-col :xs="24" :md="12">
            <div class="metrics-card">
              <div class="metrics-card-header">风险指标解释</div>
              <div class="explanation-item">
                <h4>年化波动率</h4>
                <p>衡量投资组合收益率的波动程度，波动率越高，风险越大。</p>
              </div>
              <div class="explanation-item">
                <h4>最大回撤</h4>
                <p>投资组合从峰值到谷值的最大跌幅，反映最坏情况下的损失。</p>
              </div>
              <div class="explanation-item">
                <h4>夏普比率</h4>
                <p>每承担一单位风险所获得的超额收益，比率越高，风险调整后收益越好。</p>
              </div>
              <div class="explanation-item">
                <h4>索提诺比率</h4>
                <p>仅考虑下行风险的收益风险比，更关注亏损风险。</p>
              </div>
            </div>
          </a-col>
        </a-row>
      </div>

      <!-- 资产配置 -->
      <div v-show="activeTab === 'allocation'" class="tab-content">
        <a-row :gutter="20">
          <a-col :xs="24" :md="12">
            <div class="chart-card">
              <div class="chart-card-header">
                <span class="chart-title">资产配置</span>
                <span class="chart-sub">按最新持仓市值占比</span>
              </div>
              <div id="allocationChart" class="chart-container"></div>
            </div>
          </a-col>
          <a-col :xs="24" :md="12">
            <div class="metrics-card">
              <div class="metrics-card-header">持仓明细</div>
              <a-table
                :columns="holdingColumns"
                :data-source="holdings"
                :pagination="false"
                row-key="code"
                :locale="{ emptyText: '暂无持仓' }"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'allocation'">
                    <a-progress :percent="record.allocation" :stroke-width="6" :show-info="false" stroke-color="#6366f1" style="margin-bottom: 4px; max-width: 120px" />
                    <span style="font-size: 12px; color: var(--text-secondary)">{{ record.allocation }}%</span>
                  </template>
                  <template v-else-if="column.key === 'recent_return'">
                    <span v-if="record.recent_return != null" :class="record.recent_return >= 0 ? 'profit' : 'loss'">
                      {{ record.recent_return >= 0 ? '+' : '' }}{{ record.recent_return }}%
                    </span>
                    <span v-else>—</span>
                  </template>
                </template>
              </a-table>
            </div>
          </a-col>
        </a-row>
      </div>

      <!-- 交易统计 -->
      <div v-show="activeTab === 'trading'" class="tab-content">
        <a-row :gutter="20">
          <a-col :xs="24" :md="12">
            <div class="metrics-card">
              <div class="metrics-card-header">交易统计</div>
              <div class="stat-item">
                <span class="label">总交易次数</span>
                <span class="value">{{ tradingStats.total }}次</span>
              </div>
              <div class="stat-item">
                <span class="label">买入次数</span>
                <span class="value buy">{{ tradingStats.buys }}次</span>
              </div>
              <div class="stat-item">
                <span class="label">卖出次数</span>
                <span class="value">{{ tradingStats.sells }}次</span>
              </div>
              <div class="stat-item">
                <span class="label">胜率</span>
                <span class="value muted">— 暂无卖出记录</span>
              </div>
              <div class="stat-item">
                <span class="label">盈亏比</span>
                <span class="value muted">— 暂无卖出记录</span>
              </div>
              <div class="stat-item">
                <span class="label">平均持仓天数</span>
                <span class="value muted">— 数据积累中</span>
              </div>
            </div>
          </a-col>
          <a-col :xs="24" :md="12">
            <div class="metrics-card">
              <div class="metrics-card-header">系统提示</div>
              <div class="tip-item tip-blue">
                <InfoCircleFilled />
                <span>本系统为只读查看模式，AI 仅提供分析建议，不执行任何交易</span>
              </div>
              <div class="tip-item tip-green" v-if="tradingStats.total === 0">
                <InfoCircleFilled />
                <span>当前暂无交易记录，信号出现后系统会自动记录分析建议</span>
              </div>
              <div class="tip-item tip-green" v-else>
                <CheckCircleFilled />
                <span>当前共 {{ tradingStats.total }} 笔交易记录（买入 {{ tradingStats.buys }} / 卖出 {{ tradingStats.sells }}）</span>
              </div>
              <div class="tip-item tip-amber">
                <WarningFilled />
                <span>模拟数据仅供参考学习，不构成投资建议，投资有风险</span>
              </div>
            </div>
          </a-col>
        </a-row>
      </div>
    </div>
  </div>
  </a-spin>
</template>

<style scoped>
.analysis-container {
  padding: 0 0 32px;
  max-width: 1400px;
  margin: 0 auto;
}

/* ===== Hero 霓虹横幅（与内容区同宽） ===== */
.hero {
  margin: 0 0 24px;
  padding: 36px 28px;
  border-radius: var(--radius-lg);
  background: var(--grad-hero);
  position: relative;
  overflow: hidden;
}

.hero::before {
  content: '';
  position: absolute;
  top: -60%;
  right: -10%;
  width: 420px;
  height: 420px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(167, 139, 250, 0.22), transparent 70%);
}

.hero::after {
  content: '';
  position: absolute;
  bottom: -80%;
  left: 20%;
  width: 360px;
  height: 360px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(34, 211, 238, 0.12), transparent 70%);
}

.hero-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  position: relative;
  z-index: 1;
}

.hero-tag {
  display: inline-block;
  padding: 4px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.25);
  color: #c7d2fe;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 1px;
  margin-bottom: 14px;
}

.hero h1 {
  color: #fff;
  font-size: 2.2rem;
  font-weight: 700;
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}

.hero p {
  color: rgba(255, 255, 255, 0.75);
  font-size: 14px;
}

.hero-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 26px;
  border: none;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 600;
  color: #1e1b4b;
  background: linear-gradient(135deg, #e8b13c, #d1911c);
  cursor: pointer;
  box-shadow: 0 6px 22px rgba(209, 145, 28, 0.28);
  transition: all 0.2s;
}

.hero-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 28px rgba(209, 145, 28, 0.4);
}

/* ===== 概览统计卡 ===== */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin: 0 0 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px 22px;
  background: var(--card);
  border-radius: 16px;
  box-shadow: var(--shadow);
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-hover);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #fff;
  flex-shrink: 0;
}

.stat-indigo .stat-icon { background: linear-gradient(135deg, #6366f1, #4f46e5); }
.stat-violet .stat-icon { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }
.stat-green .stat-icon { background: linear-gradient(135deg, #10b981, #059669); }
.stat-red .stat-icon { background: linear-gradient(135deg, #f43f5e, #e11d48); }

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: 0.3px;
}

.stat-green .stat-value { color: #34d399; }
.stat-red .stat-value { color: #f87171; }

/* ===== 分析面板 ===== */
.analysis-panel {
  background: var(--card);
  border-radius: 20px;
  box-shadow: var(--shadow);
  overflow: hidden;
}

.panel-header {
  padding: 18px 24px 0;
  border-bottom: 1px solid var(--border);
}

.panel-tabs {
  display: flex;
  gap: 6px;
}

.panel-tab {
  padding: 12px 18px;
  border: none;
  background: transparent;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 10px 10px 0 0;
  position: relative;
  transition: color 0.2s, background 0.2s;
}

.panel-tab:hover { color: #a5b4fc; background: rgba(129, 140, 248, 0.15); }

.panel-tab.active {
  color: #a5b4fc;
  background: rgba(129, 140, 248, 0.15);
}

.panel-tab.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 20%;
  right: 20%;
  height: 3px;
  border-radius: 3px 3px 0 0;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
}

.tab-content {
  padding: 24px;
}

/* ===== 图表卡 / 指标卡 ===== */
.chart-card {
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 18px;
  height: 100%;
}

.chart-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.chart-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
}

.chart-sub {
  font-size: 12px;
  color: var(--text-muted);
}

.chart-container {
  height: 380px;
  width: 100%;
}

.metrics-card {
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px;
  height: 100%;
  background: linear-gradient(180deg, #232a56, #1c2348);
}

.metrics-card-header {
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

/* 收益指标 */
.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 13px 6px;
  border-bottom: 1px solid var(--border);
}

.metric-item:last-child { border-bottom: none; }

.metric-item .label { color: var(--text-secondary); font-size: 13px; }

.metric-item .value { font-weight: 700; font-size: 15px; color: var(--text); }

.metric-item .value.profit { color: #34d399; }
.metric-item .value.loss { color: #f87171; }
.metric-item .value.muted { color: var(--text-muted); font-weight: 500; font-size: 13px; }

.metrics-note {
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 10px;
  background: var(--bg-soft);
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.6;
}

/* 风险指标 */
.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.metric-card {
  display: flex;
  align-items: center;
  padding: 18px;
  background: var(--card);
  border-radius: 14px;
  border: 1px solid var(--border);
  transition: transform 0.2s, box-shadow 0.2s;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}

.metric-icon {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 14px;
  color: white;
  font-size: 18px;
  flex-shrink: 0;
}

.metric-icon.volatility { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.metric-icon.drawdown { background: linear-gradient(135deg, #f56c6c 0%, #e74c3c 100%); }
.metric-icon.sharpe { background: linear-gradient(135deg, #67c23a 0%, #4caf50 100%); }
.metric-icon.sortino { background: linear-gradient(135deg, #e6a23c 0%, #f39c12 100%); }

.metric-label { font-size: 12px; color: var(--text-muted); margin-bottom: 4px; }
.metric-value { font-size: 19px; font-weight: 700; color: var(--text); }
.metric-value.loss { color: #f87171; }

/* 风险解释 */
.explanation-item { margin-bottom: 18px; }
.explanation-item h4 { font-size: 14px; color: var(--text); margin-bottom: 6px; }
.explanation-item p { font-size: 13px; color: var(--text-secondary); line-height: 1.7; }

/* 交易统计 */
.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 13px 6px;
  border-bottom: 1px solid var(--border);
}

.stat-item:last-child { border-bottom: none; }

.stat-item .label { color: var(--text-secondary); font-size: 13px; }
.stat-item .value { font-weight: 700; font-size: 15px; color: var(--text); }
.stat-item .value.buy { color: #34d399; }
.stat-item .value.muted { color: var(--text-muted); font-weight: 500; font-size: 13px; }

.tip-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.6;
}

.tip-item :deep(svg) { font-size: 17px; margin-top: 1px; flex-shrink: 0; }
.tip-blue { background: rgba(129, 140, 248, 0.15); color: #a5b4fc; }
.tip-blue :deep(svg) { color: #a5b4fc; }
.tip-green { background: rgba(52, 211, 153, 0.1); color: #6ee7b7; }
.tip-green :deep(svg) { color: #34d399; }
.tip-amber { background: rgba(251, 191, 36, 0.1); color: #fcd34d; }
.tip-amber :deep(svg) { color: #fbbf24; }

.profit { color: #34d399; font-weight: 600; }
.loss { color: #f87171; font-weight: 600; }

/* 响应式 */
@media (max-width: 1280px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .hero { padding: 28px 16px; }
  .hero-content { flex-direction: column; align-items: flex-start; gap: 16px; }
  .stats-grid { margin: 0 0 16px; }
  .analysis-panel { margin: 0; }
  .tab-content { padding: 16px; }
  .metric-grid { grid-template-columns: 1fr; }
  .chart-container { height: 300px; }
}
</style>
