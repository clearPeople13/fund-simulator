<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  WalletOutlined,
  LineChartOutlined,
  DollarOutlined,
  DashboardOutlined
} from '@ant-design/icons-vue'
import axios from 'axios'
import * as echarts from 'echarts'

const loading = ref(true)

const portfolioStats = ref({
  initial_capital: 100000,
  current_assets: 100000,
  total_return: 0,
  total_return_rate: 0
})

const holdings = ref([])
const dailyPnl = ref([]) // 每日收益明细
const fundNames = ref({})

// a-table 列配置
const tableColumns = [
  { title: '代码', dataIndex: 'fund_code', key: 'fund_code', width: 100 },
  { title: '基金名称', dataIndex: 'fund_name', key: 'fund_name' },
  { title: '类型', key: 'fund_type', width: 80 },
  { title: '份额', key: 'shares', width: 100 },
  { title: '成本价', key: 'cost_price', width: 90 },
  { title: '现价', key: 'current_price', width: 90 },
  { title: '市值', key: 'market_value', width: 110 },
  { title: '盈亏', key: 'profit_loss', width: 120 },
  { title: '收益率', key: 'profit_loss_rate', width: 100 }
]

// 每日收益明细动态列（每只持仓基金一列）
const dailyColumns = computed(() => {
  const base = [
    { title: '日期', dataIndex: 'date', key: 'date', width: 110 },
    { title: '当日盈亏', key: 'pnl', width: 110, align: 'right' },
    { title: '账户快照对照', key: 'account_pnl', width: 130, align: 'right' }
  ]
  const fundCols = Object.keys(fundNames.value).map(c => ({
    title: `${c} ${fundNames.value[c]}`,
    key: 'fund_' + c,
    align: 'right'
  }))
  return [...base, ...fundCols]
})

// 初始化资产配置图（真实持仓数据）
const initAllocationChart = () => {
  const chartDom = document.getElementById('allocationChart')
  if (!chartDom) return

  const existingChart = echarts.getInstanceByDom(chartDom)
  if (existingChart) existingChart.dispose()

  if (holdings.value.length === 0) {
    chartDom.innerHTML = '<div style="height:100%;display:flex;align-items:center;justify-content:center;color:#8b92b8;font-size:14px">暂无持仓</div>'
    return
  }

  const myChart = echarts.init(chartDom)
  const palette = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#06b6d4', '#10b981', '#f59e0b', '#3b82f6']
  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(30,41,59,0.9)',
      borderWidth: 0,
      textStyle: { color: '#f8fafc' },
      formatter: '{b}<br/>市值: ¥{c} ({d}%)'
    },
    legend: { bottom: 0, icon: 'circle', itemWidth: 8, itemHeight: 8, textStyle: { color: '#8b92b8', fontSize: 12 } },
    series: [{
      name: '持仓配置',
      type: 'pie',
      radius: ['42%', '68%'],
      center: ['50%', '44%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 15, fontWeight: 'bold', formatter: '{b}\n{d}%' } },
      data: holdings.value.map((item, index) => ({
        value: item.market_value,
        name: item.fund_name,
        itemStyle: { color: palette[index % palette.length] }
      }))
    }]
  }
  myChart.setOption(option)
  window.addEventListener('resize', () => myChart.resize())
}

// 加载真实组合数据
const loadData = async () => {
  loading.value = true
  try {
    const [pfRes, fundsRes] = await Promise.all([
      axios.get('/api/ai/portfolio'),
      axios.get('/api/funds', { params: { limit: 100 } })
    ])
    const pf = pfRes.data || {}
    const funds = (fundsRes.data && fundsRes.data.data) || []
    const fundMap = {}
    funds.forEach(f => { fundMap[f.fund_code] = f })

    const rows = []
    for (const [code, h] of Object.entries(pf.holdings || {})) {
      const fund = fundMap[code] || {}
      // 市值优先用后端持仓 market_value（fund_nav 最新净值口径）；fundMap 仅 universe top100，持仓基金可能不在其中
      const marketValue = h.market_value != null ? h.market_value : (h.shares * (fund.latest_nav != null ? fund.latest_nav : h.cost))
      const currentPrice = marketValue / h.shares
      const profit = marketValue - h.total_cost
      rows.push({
        fund_code: code,
        fund_name: h.fund_name || fund.fund_name || code,
        fund_type: fund.fund_type || '—',
        shares: h.shares,
        cost_price: h.cost,
        current_price: currentPrice,
        market_value: marketValue,
        profit_loss: h.pending_confirm ? 0 : profit,
        profit_loss_rate: h.pending_confirm ? 0 : (h.total_cost > 0 ? Number((profit / h.total_cost * 100).toFixed(2)) : 0)
      })
    }
    holdings.value = rows

    const marketValueTotal = rows.reduce((s, r) => s + r.market_value, 0)
    const currentAssets = (pf.current_capital || 0) + marketValueTotal
    const initial = pf.initial_capital || 100000
    portfolioStats.value = {
      initial_capital: initial,
      current_assets: currentAssets,
      total_return: currentAssets - initial,
      total_return_rate: initial > 0 ? Number(((currentAssets - initial) / initial * 100).toFixed(2)) : 0
    }
    // 每日收益明细（账户级跨基金按日贡献 + 账户快照对照）
    try {
      const dpRes = await axios.get('/api/ai/daily-pnl')
      if (dpRes.data && dpRes.data.list) {
        dailyPnl.value = dpRes.data.list
        fundNames.value = dpRes.data.fund_names || {}
      }
    } catch (e) {
      console.error('加载每日收益明细失败:', e)
    }
    loading.value = false
    setTimeout(() => initAllocationChart(), 100)
  } catch (error) {
    console.error('加载组合数据失败:', error)
    loading.value = false
  }
}

// 导出持仓 + 每日收益明细 CSV（纯前端 Blob 下载）
const exportCSV = () => {
  const esc = (v) => { const t = String(v ?? '').replace(/"/g, '""'); return `"${t}"` }
  const lines = []
  lines.push('持仓明细导出（' + new Date().toLocaleString() + '）')
  lines.push(['代码', '基金名称', '类型', '份额', '成本价', '现价', '市值', '盈亏', '收益率'].join(','))
  holdings.value.forEach(r => lines.push([r.fund_code, r.fund_name, r.fund_type, r.shares, r.cost_price, r.current_price, r.market_value, r.profit_loss, r.profit_loss_rate + '%'].map(esc).join(',')))
  lines.push('')
  lines.push('每日收益明细（日期,当日盈亏,账户快照对照' + Object.keys(fundNames.value).map(c => ',' + c + ' ' + fundNames.value[c]).join('') + '）')
  dailyPnl.value.forEach(r => {
    const fundCols = Object.keys(fundNames.value).map(c => r.funds && r.funds[c] != null ? r.funds[c] : '')
    lines.push([r.date, r.pnl, r.account_pnl != null ? r.account_pnl : '待更新', ...fundCols].join(','))
  })
  const blob = new Blob(['\ufeff' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '组合明细_' + new Date().toISOString().slice(0, 10) + '.csv'
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <a-spin :spinning="loading">
  <div class="portfolio-container">
    <!-- Hero 头图 -->
    <div class="page-hero">
      <div class="hero-inner">
        <div>
          <div class="hero-tag">我的组合</div>
          <h1>投资组合</h1>
          <p class="hero-desc">查看您的持仓情况和资产配置</p>
        </div>
      </div>
    </div>

    <!-- 组合概览 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon icon-indigo"><WalletOutlined /></div>
        <div class="stat-body">
          <div class="stat-label">初始资金</div>
          <div class="stat-value">¥{{ portfolioStats.initial_capital.toLocaleString() }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon icon-violet"><LineChartOutlined /></div>
        <div class="stat-body">
          <div class="stat-label">当前资产</div>
          <div class="stat-value">¥{{ portfolioStats.current_assets.toLocaleString() }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" :class="portfolioStats.total_return >= 0 ? 'icon-green' : 'icon-red'"><DollarOutlined /></div>
        <div class="stat-body">
          <div class="stat-label">累计收益</div>
          <div class="stat-value" :class="portfolioStats.total_return >= 0 ? 'up' : 'down'">
            {{ portfolioStats.total_return >= 0 ? '+' : '' }}¥{{ portfolioStats.total_return.toLocaleString() }}
          </div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon icon-amber"><DashboardOutlined /></div>
        <div class="stat-body">
          <div class="stat-label">收益率</div>
          <div class="stat-value" :class="portfolioStats.total_return_rate >= 0 ? 'up' : 'down'">
            {{ portfolioStats.total_return_rate >= 0 ? '+' : '' }}{{ portfolioStats.total_return_rate }}%
          </div>
        </div>
      </div>
    </div>

    <a-row :gutter="20">
      <!-- 持仓列表 -->
      <a-col :xs="24" :md="16">
        <a-card :bordered="false">
          <template #title>
            <div class="card-header">
              <span class="block-title-no-margin">持仓明细</span>
              <span>
                <a-tag>{{ holdings.length }} 只</a-tag>
                <a-button size="small" style="margin-left:8px" @click="exportCSV">导出 CSV</a-button>
              </span>
            </div>
          </template>
          <a-table
            :columns="tableColumns"
            :data-source="holdings"
            :pagination="false"
            row-key="fund_code"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'fund_type'">
                <a-tag>{{ record.fund_type }}</a-tag>
              </template>
              <template v-else-if="column.key === 'shares'">
                {{ record.shares.toLocaleString() }}
              </template>
              <template v-else-if="column.key === 'cost_price'">
                ¥{{ record.cost_price.toFixed(2) }}
              </template>
              <template v-else-if="column.key === 'current_price'">
                ¥{{ record.current_price.toFixed(2) }}
              </template>
              <template v-else-if="column.key === 'market_value'">
                ¥{{ record.market_value.toLocaleString() }}
              </template>
              <template v-else-if="column.key === 'profit_loss'">
                <template v-if="record.pending_confirm">— <a-tag style="font-size:10px;line-height:14px;margin-left:4px;">T+1</a-tag></template>
                <span v-else :class="record.profit_loss >= 0 ? 'profit' : 'loss'">
                  {{ record.profit_loss >= 0 ? '+' : '' }}¥{{ record.profit_loss.toLocaleString() }}
                </span>
              </template>
              <template v-else-if="column.key === 'profit_loss_rate'">
                <span v-if="record.pending_confirm">—</span>
                <span v-else :class="record.profit_loss_rate >= 0 ? 'profit' : 'loss'">
                  {{ record.profit_loss_rate >= 0 ? '+' : '' }}{{ record.profit_loss_rate }}%
                </span>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>

      <!-- 资产配置 -->
      <a-col :xs="24" :md="8">
        <a-card :bordered="false" class="allocation-card" title="资产配置">
          <div id="allocationChart" class="chart-container"></div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 每日收益明细（账户级跨基金按日贡献） -->
    <a-card :bordered="false" style="margin-top:20px">
      <template #title>
        <div class="card-header">
          <span class="block-title-no-margin">📅 每日收益明细</span>
          <a-tag>当日盈亏 = 收盘份额 × 净值变动（买入当日 T+1 无收益）</a-tag>
        </div>
      </template>
      <a-table
        :columns="dailyColumns"
        :data-source="dailyPnl"
        :pagination="false"
        row-key="date"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'pnl'">
            <span :class="record.pnl >= 0 ? 'profit' : 'loss'">
              <template v-if="record.pnl > 0">+</template>{{ record.pnl.toFixed(2) }}
            </span>
          </template>
          <template v-else-if="column.key === 'account_pnl'">
            <span v-if="record.account_pnl == null" style="color:#64748b">待更新</span>
            <span v-else :class="record.account_pnl >= 0 ? 'profit' : 'loss'">
              <template v-if="record.account_pnl > 0">+</template>{{ Number(record.account_pnl).toFixed(2) }}
            </span>
          </template>
          <template v-else-if="column.key.startsWith('fund_')">
            <template v-if="record.funds && record.funds[column.key.slice(5)] != null">
              <span :class="record.funds[column.key.slice(5)] >= 0 ? 'profit' : 'loss'">
                <template v-if="record.funds[column.key.slice(5)] > 0">+</template>{{ record.funds[column.key.slice(5)].toFixed(2) }}
              </span>
            </template>
            <template v-else><span style="color:#475569">—</span></template>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
  </a-spin>
</template>

<style scoped>
.portfolio-container {
  padding: 0 0 32px;
  max-width: 1400px;
  margin: 0 auto;
}

.stat-body {
  flex: 1;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.block-title-no-margin {
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
}

.allocation-card {
  height: 100%;
}

.chart-container {
  height: 350px;
  width: 100%;
}

.profit {
  color: #34d399;
  font-weight: 600;
}

.loss {
  color: #f87171;
  font-weight: 600;
}
</style>
