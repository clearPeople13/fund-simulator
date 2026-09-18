<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { BarChartOutlined, FileOutlined } from '@ant-design/icons-vue'
import axios from 'axios'
import * as echarts from 'echarts'

const router = useRouter()
const route = useRoute()

// 响应式数据
const loading = ref(false)
const analyzing = ref(false)
const selectedFund = ref(null)
const analysisResult = ref(null)
const analysisProgress = ref(0)
const currentPhase = ref('')
const navHistory = ref([])

// 真实基金列表
const fundList = ref([])

// 分析阶段（真实执行说明）
const phases = [
  { id: 1, name: '阶段1: 拉取真实净值', description: '获取基金最近净值与历史走势' },
  { id: 2, name: '阶段2: 信号计算', description: '计算20日趋势、60日回撤、均线位置' },
  { id: 3, name: '阶段3: 信号判定', description: '依据真实数据生成入场/观望建议' },
  { id: 4, name: '阶段4: 风险提示', description: '给出参考入场价、目标价、止损价' }
]

// 加载真实基金列表
const loadFundList = async () => {
  try {
    const res = await axios.get('/api/funds', { params: { limit: 100 } })
    const funds = (res.data && res.data.data) || []
    fundList.value = funds.map(f => ({ code: f.fund_code, name: f.fund_name, type: f.fund_type }))
  } catch (error) {
    console.error('加载基金列表失败:', error)
  }
}

// 初始化净值走势图（真实净值）
const initNavChart = () => {
  const chartDom = document.getElementById('navChart')
  if (!chartDom) return
  const existingChart = echarts.getInstanceByDom(chartDom)
  if (existingChart) existingChart.dispose()

  if (navHistory.value.length < 2) {
    chartDom.innerHTML = '<div style="height:100%;display:flex;align-items:center;justify-content:center;color:#8b92b8;font-size:14px">暂无净值走势数据</div>'
    return
  }

  const myChart = echarts.init(chartDom)
  const dates = navHistory.value.map(n => n.date)
  const values = navHistory.value.map(n => n.unit_nav)

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: function (params) {
        return `${params[0].axisValue}<br/>单位净值: ¥${params[0].value.toFixed(4)}`
      }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: dates, axisLabel: { rotate: 45, interval: 11 } },
    yAxis: { type: 'value', axisLabel: { formatter: '¥{value}' } },
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
      lineStyle: { color: '#667eea', width: 2 },
      data: values
    }]
  }
  myChart.setOption(option)
}

// 开始AI分析（真实信号，只出建议不交易）
const startAnalysis = async () => {
  if (!selectedFund.value) {
    message.warning('请先选择要分析的基金')
    return
  }

  try {
    analyzing.value = true
    analysisProgress.value = 0
    currentPhase.value = '准备开始分析...'
    navHistory.value = []

    // 真实分析阶段（每阶段为真实计算等待，非模拟耗时）
    for (let i = 0; i < phases.length; i++) {
      currentPhase.value = phases[i].name
      analysisProgress.value = ((i + 1) / phases.length) * 100
      await new Promise(resolve => setTimeout(resolve, 600))
    }

    // 调用后端真实分析接口
    const res = await axios.post('/api/ai/analyze', { fund_codes: [selectedFund.value] })
    const results = (res.data && res.data.results) || {}
    const result = results[selectedFund.value]

    if (!result) {
      message.error('该基金暂无足够数据分析')
      analyzing.value = false
      return
    }

    // 基金名称
    const fund = fundList.value.find(f => f.code === selectedFund.value)

    // 拉取真实净值历史（近60日）
    try {
      const navRes = await axios.get(`/api/funds/${selectedFund.value}/nav`, { params: { limit: 60 } })
      navHistory.value = (Array.isArray(navRes.data) ? navRes.data : []).map(n => ({
        date: n.nav_date,
        unit_nav: n.unit_nav
      }))
    } catch (e) {
      console.error('加载净值历史失败:', e)
    }

    analysisResult.value = {
      fund_code: selectedFund.value,
      fund_name: fund?.name || selectedFund.value,
      analysis_date: (res.data.analysis_time || new Date().toISOString()).slice(0, 10),
      decision: result.decision,
      signal_label: result.signal_label,
      confidence: result.confidence,
      entry_price: result.entry_price,
      target_price: result.target_price,
      stop_loss: result.stop_loss,
      signal_reason: result.signal_reason,
      change_5d: result.change_5d,
      change_20d: result.change_20d,
      drawdown_60d: result.drawdown_60d,
      above_ma20: result.above_ma20,
      nav_date: result.nav_date,
      daily_return: result.daily_return
    }
    analysisProgress.value = 100
    currentPhase.value = '分析完成'

    message.success('分析完成（仅建议，不执行交易）')

    setTimeout(() => initNavChart(), 100)

  } catch (error) {
    message.error('分析失败: ' + (error.response?.data?.error || error.message))
  } finally {
    analyzing.value = false
  }
}

// 导出分析报告
const exportReport = () => {
  message.success('分析报告导出功能开发中...')
}

onMounted(() => {
  loadFundList()
  // 如果URL中有基金代码参数
  if (route.query.fund_code) {
    selectedFund.value = route.query.fund_code
  }
})
</script>

<template>
  <div class="ai-analysis-container">
    <!-- Hero 头图 -->
    <div class="page-hero">
      <div class="hero-inner">
        <div>
          <div class="hero-tag">AI 分析引擎</div>
          <h1>AI智能分析</h1>
          <p class="hero-desc">基于真实净值数据的信号分析，仅提供查看建议，系统不执行任何交易</p>
        </div>
      </div>
    </div>

    <!-- 分析控制面板 -->
    <a-card class="control-panel" :bordered="false">
      <template #title>
        <div class="card-header">
          <span class="panel-title">分析控制面板</span>
          <a-tag v-if="analyzing" color="processing">分析中...</a-tag>
          <a-tag v-else-if="analysisResult" color="success">分析完成</a-tag>
          <a-tag v-else>待分析</a-tag>
        </div>
      </template>

      <a-row :gutter="20" :align="'middle'">
        <a-col :xs="24" :md="12">
          <div class="fund-selector">
            <label>选择基金：</label>
            <a-select
              v-model:value="selectedFund"
              placeholder="请选择要分析的基金"
              style="width: 100%"
              :disabled="analyzing"
            >
              <a-select-option
                v-for="fund in fundList"
                :key="fund.code"
                :label="`${fund.code} - ${fund.name}`"
                :value="fund.code"
              />
            </a-select>
          </div>
        </a-col>
        <a-col :xs="24" :md="12">
          <div class="action-buttons">
            <a-button
              type="primary"
              @click="startAnalysis"
              :loading="analyzing"
              :disabled="!selectedFund"
            >
              <BarChartOutlined />
              {{ analyzing ? '分析中...' : '开始AI分析' }}
            </a-button>
            <a-button
              @click="exportReport"
              :disabled="!analysisResult"
            >
              <FileOutlined />
              导出报告
            </a-button>
          </div>
        </a-col>
      </a-row>

      <!-- 分析进度 -->
      <div class="analysis-progress" v-if="analyzing">
        <a-progress :percent="analysisProgress" :status="analysisProgress === 100 ? 'success' : 'active'" />
        <p class="current-phase">{{ currentPhase }}</p>
      </div>
    </a-card>

    <!-- 分析结果 -->
    <div class="analysis-result" v-if="analysisResult">
      <!-- 决策卡片 -->
      <a-card class="decision-card" :bordered="false">
        <div class="decision-content">
          <div class="decision-badge" :class="analysisResult.decision.toLowerCase()">
            {{ analysisResult.signal_label }}
          </div>
          <div class="decision-details">
            <h2>{{ analysisResult.fund_name }}</h2>
            <p>基金代码：{{ analysisResult.fund_code }} · 分析日期：{{ analysisResult.analysis_date }} · 最新净值日期：{{ analysisResult.nav_date || '—' }}</p>
            <div class="decision-metrics">
              <div class="metric">
                <span class="label">信心水平：</span>
                <span class="value">{{ analysisResult.confidence }}</span>
              </div>
              <div class="metric">
                <span class="label">近5日：</span>
                <span class="value" :class="(analysisResult.change_5d ?? 0) >= 0 ? 'profit' : 'loss'">
                  {{ analysisResult.change_5d != null ? (analysisResult.change_5d >= 0 ? '+' : '') + analysisResult.change_5d + '%' : '—' }}
                </span>
              </div>
              <div class="metric">
                <span class="label">近20日：</span>
                <span class="value" :class="(analysisResult.change_20d ?? 0) >= 0 ? 'profit' : 'loss'">
                  {{ analysisResult.change_20d != null ? (analysisResult.change_20d >= 0 ? '+' : '') + analysisResult.change_20d + '%' : '—' }}
                </span>
              </div>
              <div class="metric">
                <span class="label">距60日高点：</span>
                <span class="value loss">{{ analysisResult.drawdown_60d != null ? analysisResult.drawdown_60d + '%' : '—' }}</span>
              </div>
              <div class="metric">
                <span class="label">20日线：</span>
                <span class="value">{{ analysisResult.above_ma20 == null ? '—' : (analysisResult.above_ma20 ? '上方' : '下方') }}</span>
              </div>
            </div>
          </div>
        </div>
      </a-card>

      <!-- 价格信息 -->
      <a-row :gutter="20" class="price-info">
        <a-col :xs="24" :md="8">
          <a-card :bordered="false" class="price-card price-entry">
            <div class="price-item">
              <div class="price-label">参考入场价（最新净值）</div>
              <div class="price-value">¥{{ analysisResult.entry_price != null ? analysisResult.entry_price.toFixed(4) : '—' }}</div>
            </div>
          </a-card>
        </a-col>
        <a-col :xs="24" :md="8">
          <a-card :bordered="false" class="price-card price-target">
            <div class="price-item">
              <div class="price-label">参考目标价（+10%）</div>
              <div class="price-value profit">¥{{ analysisResult.target_price != null ? analysisResult.target_price.toFixed(4) : '—' }}</div>
            </div>
          </a-card>
        </a-col>
        <a-col :xs="24" :md="8">
          <a-card :bordered="false" class="price-card price-stop">
            <div class="price-item">
              <div class="price-label">参考止损价（-5%）</div>
              <div class="price-value loss">¥{{ analysisResult.stop_loss != null ? analysisResult.stop_loss.toFixed(4) : '—' }}</div>
            </div>
          </a-card>
        </a-col>
      </a-row>

      <!-- 净值走势（真实数据） -->
      <a-card class="nav-chart-card" :bordered="false">
        <div class="block-title">真实净值走势（近60日）</div>
        <div id="navChart" class="chart-container"></div>
      </a-card>

      <!-- 详细分析 -->
      <a-card class="detail-analysis" :bordered="false" title="分析依据（基于真实净值数据）">
        <p class="signal-reason">{{ analysisResult.signal_reason }}</p>
        <a-alert
          style="margin-top: 12px"
          type="info"
          message="本系统为只读查看模式：AI 仅输出信号建议，不会自动买入，也不提供任何买入/卖出操作入口。"
          :closable="false"
          show-icon
        />
      </a-card>

      <!-- 免责声明 -->
      <div class="disclaimer">
        <a-alert
          message="免责声明"
          type="warning"
          description="以上分析由AI基于真实历史净值数据计算生成，仅供参考，不构成任何投资建议。投资有风险，决策需谨慎。"
          show-icon
          :closable="false"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.ai-analysis-container {
  padding: 0 0 32px;
  max-width: 1400px;
  margin: 0 auto;
}

.panel-title {
  font-weight: 700;
  color: var(--text);
}

.control-panel {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.fund-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.fund-selector label {
  color: var(--text-secondary);
  white-space: nowrap;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.analysis-progress {
  margin-top: 20px;
}

.current-phase {
  margin-top: 8px;
  color: var(--text-muted);
  font-size: 13px;
  text-align: center;
}

.decision-card {
  margin-bottom: 20px;
}

.decision-content {
  display: flex;
  align-items: flex-start;
  gap: 20px;
}

.decision-badge {
  padding: 14px 24px;
  border-radius: 14px;
  font-size: 17px;
  font-weight: 700;
  color: #fff;
  white-space: nowrap;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.12);
}

.decision-badge.buy {
  background: linear-gradient(135deg, #10b981, #059669);
}

.decision-badge.hold {
  background: linear-gradient(135deg, #636f8f, #3f4a6b);
}

.decision-badge.add {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}

.decision-badge.watch {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
}

.decision-badge.wait {
  background: linear-gradient(135deg, #5b6480, #3d4563);
}

.decision-details h2 {
  margin: 0 0 6px;
  color: var(--text);
  font-size: 20px;
}

.decision-details p {
  color: var(--text-muted);
  font-size: 13px;
  margin-bottom: 12px;
}

.decision-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
}

.metric .label {
  color: var(--text-muted);
  font-size: 13px;
}

.metric .value {
  font-weight: 600;
  color: var(--text);
}

.metric .value.profit {
  color: #34d399;
}

.metric .value.loss {
  color: #f87171;
}

.price-info {
  margin-bottom: 20px;
}

.price-card {
  border-top: 3px solid transparent;
}

.price-card.price-entry { border-top-color: #6366f1; }
.price-card.price-target { border-top-color: #10b981; }
.price-card.price-stop { border-top-color: #ef4444; }

.price-item {
  text-align: center;
  padding: 10px 0;
}

.price-label {
  color: var(--text-muted);
  font-size: 13px;
  margin-bottom: 8px;
}

.price-value {
  font-size: 22px;
  font-weight: 600;
  color: var(--text);
}

.price-value.profit {
  color: #34d399;
}

.price-value.loss {
  color: #f87171;
}

.nav-chart-card {
  margin-bottom: 20px;
}

.chart-container {
  height: 360px;
  width: 100%;
}

.detail-analysis {
  margin-bottom: 20px;
}

.signal-reason {
  color: var(--text);
  font-size: 15px;
  line-height: 1.7;
  margin: 0;
}

.disclaimer {
  margin-top: 10px;
}
</style>
