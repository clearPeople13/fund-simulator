<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { LeftOutlined, ThunderboltOutlined } from '@ant-design/icons-vue'
import axios from 'axios'
import * as echarts from 'echarts'

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const fundCode = ref(route.params.code)
const fundInfo = ref(null)
const fundReturns = ref([])

// a-table 列配置（最近净值）
const navColumns = [
  { title: '日期', dataIndex: 'date', key: 'date', width: 150 },
  { title: '单位净值', key: 'unit_nav', width: 150 },
  { title: '累计净值', key: 'acc_nav', width: 150 },
  { title: '日增长率', key: 'daily_return', width: 150 }
]

// 初始化净值走势图（真实净值数据）
const initNavChart = () => {
  const chartDom = document.getElementById('navChart')
  if (!chartDom) return

  const existingChart = echarts.getInstanceByDom(chartDom)
  if (existingChart) existingChart.dispose()

  const myChart = echarts.init(chartDom)
  const navData = fundInfo.value?.nav_history || []

  const dates = navData.map(item => item.date)
  const navValues = navData.map(item => item.unit_nav)

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(30,41,59,0.9)',
      borderWidth: 0,
      textStyle: { color: '#f8fafc' },
      formatter: function (params) {
        return `${params[0].axisValue}<br/>单位净值: ¥${params[0].value.toFixed(4)}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLine: { lineStyle: { color: '#2c3466' } },
      axisLabel: {
        color: '#8b92b8',
        rotate: 45,
        interval: 14
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#8b92b8',
        formatter: '¥{value}'
      },
      splitLine: { lineStyle: { color: '#252c56' } }
    },
    series: [{
      name: '单位净值',
      type: 'line',
      smooth: true,
      symbol: 'none',
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(102, 126, 234, 0.3)' },
          { offset: 1, color: 'rgba(102, 126, 234, 0.05)' }
        ])
      },
      lineStyle: {
        color: '#667eea',
        width: 2
      },
      data: navValues
    }]
  }

  myChart.setOption(option)
  window.addEventListener('resize', () => myChart.resize())
}

// 加载基金详情（真实数据）
const loadFundDetail = async () => {
  try {
    loading.value = true
    // 基金基本信息（优先系统跟踪库；未跟踪时由全市场基金库兜底）
    const fundRes = await axios.get(`/api/funds/${fundCode.value}`)
    const fund = fundRes.data || {}
    const tracked = fund.tracked !== false
    // 净值历史（真实，仅已跟踪基金有）
    const navRes = await axios.get(`/api/funds/${fundCode.value}/nav`, { params: { limit: 120 } })
    const navRows = Array.isArray(navRes.data) ? navRes.data : []
    // 区间涨跌幅（支付宝式）
    let returnsData = []
    try {
      const retRes = await axios.get(`/api/funds/${fundCode.value}/returns`)
      if (retRes.data && Array.isArray(retRes.data.periods)) returnsData = retRes.data.periods
    } catch (e) { console.warn('加载区间涨跌幅失败:', e.message) }
    fundReturns.value = returnsData

    fundInfo.value = {
      fund_code: fund.fund_code || fundCode.value,
      fund_name: fund.fund_name || fundCode.value,
      fund_type: fund.fund_type || '—',
      manager: fund.manager || '—',
      inception_date: fund.inception_date || '—',
      benchmark: fund.benchmark || '—',
      tracked,
      latest_nav: fund.latest_nav != null ? fund.latest_nav : null,
      latest_nav_date: fund.latest_nav_date || '',
      recent_return: fund.recent_return != null ? fund.recent_return : null,
      scale: fund.scale != null ? fund.scale : null,
      nav_history: navRows.map(n => ({
        date: n.nav_date,
        unit_nav: n.unit_nav,
        acc_nav: n.acc_nav,
        daily_return: n.daily_return
      }))
    }
    loading.value = false

    setTimeout(() => initNavChart(), 100)
  } catch (error) {
    console.error('加载基金详情失败:', error)
    loading.value = false
  }
}

// 涨跌幅条形：正右负左，宽度按最大绝对值归一化（半幅 50%）
const returnsMax = (list) => Math.max(...list.map(p => Math.abs(p.value || 0)), 1e-6)
const retWidth = (v, max) => Math.min(Math.abs(v) / max * 50, 50)

// AI分析
const goToAIAnalysis = () => {
  router.push({ path: '/ai-analysis', query: { fund_code: fundCode.value } })
}

onMounted(() => {
  loadFundDetail()
})
</script>

<template>
  <a-spin :spinning="loading">
  <div class="fund-detail-container">
    <!-- Hero 头图 -->
    <div class="page-hero" v-if="fundInfo">
      <div class="hero-inner">
        <div>
          <div class="hero-tag">{{ fundInfo.fund_code }} · {{ fundInfo.fund_type }}</div>
          <h1>{{ fundInfo.fund_name }}</h1>
          <p class="hero-desc">基金详细信息与真实净值走势</p>
        </div>
        <div class="hero-actions">
          <button class="hero-back" @click="router.push('/funds')">
            <LeftOutlined /> 返回列表
          </button>
          <button class="hero-btn" @click="goToAIAnalysis">
            <ThunderboltOutlined /> AI分析
          </button>
        </div>
      </div>
    </div>

    <template v-if="fundInfo">
      <!-- 基金基本信息 -->
      <a-row :gutter="20">
        <a-col :xs="24" :md="16">
          <a-card :bordered="false" class="chart-card">
            <div class="block-title">净值走势</div>
            <a-alert
              v-if="fundInfo && !fundInfo.tracked"
              type="info"
              show-icon
              message="该基金暂未纳入 AI 跟踪：无 AI 信号与操作记录。可在基金库点击 ☆ 观察 纳入跟踪后查看入场建议与信号"
              style="margin-bottom: 12px; border-radius: 8px"
            />
            <div id="navChart" class="chart-container"></div>
          </a-card>
        </a-col>
        <a-col :xs="24" :md="8">
          <a-card :bordered="false" class="info-card" title="基金信息">
            <div class="info-list">
              <div class="info-item">
                <span class="label">基金代码</span>
                <span class="value">{{ fundInfo.fund_code }}</span>
              </div>
              <div class="info-item">
                <span class="label">基金类型</span>
                <span class="value"><a-tag color="blue">{{ fundInfo.fund_type }}</a-tag></span>
              </div>
              <div class="info-item">
                <span class="label">基金经理</span>
                <span class="value">{{ fundInfo.manager }}</span>
              </div>
              <div class="info-item">
                <span class="label">成立日期</span>
                <span class="value">{{ fundInfo.inception_date }}</span>
              </div>
              <div class="info-item" v-if="fundInfo.latest_nav != null">
                <span class="label">最新净值</span>
                <span class="value">¥{{ fundInfo.latest_nav }}<span class="nav-date" v-if="fundInfo.latest_nav_date">（{{ fundInfo.latest_nav_date }}）</span></span>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>

      <!-- 业绩基准 -->
      <a-card :bordered="false" class="benchmark-card" title="业绩比较基准">
        <p class="benchmark-text">{{ fundInfo.benchmark }}</p>
      </a-card>

      <!-- 涨跌幅（支付宝式横向条形） -->
      <a-card :bordered="false" class="returns-card">
        <template #title>
          <div class="block-title-inline">涨跌幅</div>
          <span class="returns-sub" v-if="fundReturns.length">数据截至 {{ fundReturns[0].end_date }}</span>
        </template>
        <div v-if="fundReturns.length" class="returns-list">
          <div class="ret-row" v-for="p in fundReturns" :key="p.label">
            <span class="ret-label">{{ p.label }}</span>
            <div class="ret-track">
              <div class="ret-zero"></div>
              <div
                class="ret-fill"
                :class="p.value != null && p.value >= 0 ? 'up' : 'down'"
                :style="p.value != null ? { width: retWidth(p.value, returnsMax(fundReturns)) + '%', left: p.value >= 0 ? '50%' : 'auto', right: p.value >= 0 ? 'auto' : (50 - retWidth(p.value, returnsMax(fundReturns))) + '%' } : { display: 'none' }"
                :title="p.value != null && p.start_date ? (p.start_date + ' → ' + p.end_date) : '数据不足'"
              ></div>
            </div>
            <span class="ret-value" :class="p.value != null ? (p.value >= 0 ? 'profit' : 'loss') : ''">
              <template v-if="p.value != null">{{ p.value >= 0 ? '+' : '' }}{{ p.value }}%</template>
              <template v-else>—</template>
            </span>
          </div>
        </div>
        <div v-else class="returns-empty">暂无足够净值数据</div>
      </a-card>

      <!-- 最近净值 -->
      <a-card :bordered="false" title="最近净值">
        <a-table
          :columns="navColumns"
          :data-source="fundInfo.nav_history.slice(0, 10)"
          :pagination="false"
          row-key="date"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'unit_nav'">
              ¥{{ record.unit_nav != null ? record.unit_nav.toFixed(4) : '—' }}
            </template>
            <template v-else-if="column.key === 'acc_nav'">
              ¥{{ record.acc_nav != null ? record.acc_nav.toFixed(4) : '—' }}
            </template>
            <template v-else-if="column.key === 'daily_return'">
              <span v-if="record.daily_return != null" :class="record.daily_return >= 0 ? 'profit' : 'loss'">
                {{ record.daily_return >= 0 ? '+' : '' }}{{ record.daily_return }}%
              </span>
              <span v-else>—</span>
            </template>
          </template>
        </a-table>
      </a-card>
    </template>
  </div>
  </a-spin>
</template>

<style scoped>
.fund-detail-container {
  padding: 0 0 32px;
  max-width: 1400px;
  margin: 0 auto;
}

/* Hero 操作按钮 */
.hero-actions {
  display: flex;
  gap: 10px;
}

.hero-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 11px 20px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 999px;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: background 0.2s;
}

.hero-back:hover {
  background: rgba(255, 255, 255, 0.2);
}

.chart-card {
  margin-bottom: 20px;
  height: 100%;
}

.chart-card .block-title {
  font-weight: 600;
  color: var(--text);
  margin-bottom: 12px;
}

.chart-container {
  height: 400px;
  width: 100%;
}

.info-card {
  height: 100%;
}

.info-card :deep(.ant-card-head-title) {
  font-weight: 600;
  color: var(--text);
}

.info-list {
  display: flex;
  flex-direction: column;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 13px 0;
  border-bottom: 1px solid var(--border);
}

.info-item:last-child {
  border-bottom: none;
}

.info-item .label {
  color: var(--text-muted);
  font-size: 13px;
}

.info-item .value {
  color: var(--text);
  font-weight: 500;
}

.benchmark-card {
  margin-bottom: 20px;
}

.benchmark-card :deep(.ant-card-head-title) {
  font-weight: 600;
  color: var(--text);
}

.benchmark-text {
  color: var(--text-secondary);
  line-height: 1.8;
}

.profit {
  color: #34d399;
  font-weight: 600;
}

.loss {
  color: #f87171;
  font-weight: 600;
}

/* 涨跌幅（支付宝式） */
.returns-card { margin-bottom: 20px; }
.block-title-inline { display: inline-block; font-size: 15px; font-weight: 600; color: var(--text, #e8ebff); }
.returns-sub { margin-left: 10px; font-size: 12px; color: #8b92b8; }
.returns-list { display: flex; flex-direction: column; gap: 14px; padding: 4px 8px 8px; }
.ret-row { display: flex; align-items: center; gap: 14px; }
.ret-label { width: 64px; font-size: 13px; color: #a5adcf; flex-shrink: 0; }
.ret-track { position: relative; flex: 1; height: 16px; background: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden; }
.ret-zero { position: absolute; top: 0; bottom: 0; left: 50%; width: 1px; background: rgba(139,146,184,0.5); z-index: 2; }
.ret-fill { position: absolute; top: 2px; bottom: 2px; border-radius: 3px; transition: width 0.3s; }
.ret-fill.up { background: linear-gradient(90deg, rgba(52,211,153,0.5), #34d399); }
.ret-fill.down { background: linear-gradient(270deg, rgba(248,113,113,0.5), #f87171); }
.ret-value { width: 84px; text-align: right; font-size: 13px; font-weight: 600; font-variant-numeric: tabular-nums; flex-shrink: 0; }
.returns-empty { padding: 12px 0; color: #8b92b8; font-size: 13px; }
</style>
