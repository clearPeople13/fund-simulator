<template>
  <div class="market-page">
    <div class="page-hero">
      <div class="hero-inner">
        <div>
          <div class="hero-tag">📈 市场行情</div>
          <h1>市场温度与指数走势</h1>
          <p class="hero-desc">基准指数（沪深300）走势 · 全市场基金涨跌统计 · AI 眼中的市场温度</p>
        </div>
        <div class="hero-actions">
          <button class="hero-btn" @click="loadMarket"><SyncOutlined /> 刷新</button>
        </div>
      </div>
    </div>

    <a-spin :spinning="loading">
      <template v-if="market">
        <!-- 温度 + 统计 -->
        <div class="stat-grid">
          <div class="stat-card temp-card">
            <div class="stat-label">市场温度（AI 判定）</div>
            <div class="temp-value">
              <span class="temp-badge" :class="'temp-' + (market.market_env ? market.market_env.temperature : 'neutral')">
                {{ tempText }}
              </span>
              <span class="temp-detail" v-if="market.market_env">
                基金平均 {{ fmt(market.market_env.avg_fund_chg) }}% · 指数 {{ fmt(market.market_env.bench_chg) }}% · {{ market.market_env.date }}
              </span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-label">全市场基金</div>
            <div class="stat-big">{{ market.stats.fund_count.toLocaleString() }} 只</div>
            <div class="stat-sub">含净值数据的基金样本</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">今日涨跌分布</div>
            <div class="stat-row">
              <span class="s-up">涨 {{ market.stats.up }}</span>
              <span class="s-down">跌 {{ market.stats.down }}</span>
              <span class="s-flat">平 {{ market.stats.flat }}</span>
            </div>
            <div class="stat-sub">上涨占比 {{ market.stats.up_pct }}% · 平均 {{ fmt(market.stats.avg_return) }}%</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">近5日指数涨跌</div>
            <div class="bench-5d">
              <span v-for="(b, i) in market.stats.bench_5d" :key="i" class="d5-item" :class="b.change_pct >= 0 ? 'profit' : 'loss'">
                {{ b.date.slice(5) }} {{ b.change_pct >= 0 ? '+' : '' }}{{ b.change_pct }}%
              </span>
            </div>
          </div>
        </div>

        <!-- 指数走势折线 -->
        <div class="card chart-card">
          <div class="card-header">
            <h3>沪深300 指数走势（近 {{ market.benchmark.length }} 个交易日）</h3>
            <span class="badge neutral" v-if="market.market_env">最新 {{ fmt(market.market_env.bench_chg) }}%</span>
          </div>
          <div id="benchChart" class="chart-container"></div>
        </div>
      </template>
    </a-spin>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import { SyncOutlined } from '@ant-design/icons-vue'

const loading = ref(false)
const market = ref(null)

const tempText = computed(() => {
  const t = market.value && market.value.market_env ? market.value.market_env.temperature : 'neutral'
  return ({ neutral: '🟡 中性', hot: '🔥 偏热', cold: '🧊 偏冷' })[t] || '🟡 中性'
})
const fmt = (v) => (v == null ? '—' : (Number(v) > 0 ? '+' : '') + Number(v).toFixed(2))

const loadMarket = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/market/overview', { params: { days: 90 } })
    market.value = res.data || null
    setTimeout(() => initBenchChart(), 80)
  } catch (e) {
    console.error('加载市场行情失败:', e.message)
  } finally {
    loading.value = false
  }
}

const initBenchChart = () => {
  const dom = document.getElementById('benchChart')
  if (!dom || !market.value) return
  const bench = market.value.benchmark || []
  const chart = echarts.init(dom)
  chart.setOption({
    backgroundColor: 'transparent',
    grid: { left: 60, right: 20, top: 40, bottom: 40 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15,20,40,0.95)',
      borderColor: 'rgba(99,102,241,0.4)',
      textStyle: { color: '#e2e8f0', fontSize: 12 },
      formatter: (ps) => {
        const p = ps[0]
        const item = bench[p.dataIndex]
        return `${p.axisValue}<br/>点位：${Number(item.value).toFixed(2)}<br/>涨跌：${item.change_pct >= 0 ? '+' : ''}${Number(item.change_pct).toFixed(2)}%`
      }
    },
    xAxis: {
      type: 'category',
      data: bench.map(b => b.date),
      axisLine: { lineStyle: { color: 'rgba(148,163,184,0.3)' } },
      axisLabel: { color: '#94a3b8', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      scale: true,
      splitLine: { lineStyle: { color: 'rgba(148,163,184,0.12)' } },
      axisLabel: { color: '#94a3b8', fontSize: 11 }
    },
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 16, bottom: 6, borderColor: 'transparent', backgroundColor: 'rgba(148,163,184,0.12)' }],
    series: [{
      name: '沪深300',
      type: 'line',
      smooth: true,
      symbol: 'none',
      lineStyle: { color: '#818cf8', width: 2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(129,140,248,0.35)' },
          { offset: 1, color: 'rgba(129,140,248,0.02)' }
        ])
      },
      data: bench.map(b => Number(b.value))
    }]
  })
  chart.on('click', () => {})
}

onMounted(loadMarket)
</script>

<style scoped>
.market-page { max-width: 1200px; margin: 0 auto; padding: 16px; }
.page-hero { background: linear-gradient(135deg, rgba(99,102,241,0.18), rgba(56,189,248,0.08)); border: 1px solid rgba(99,102,241,0.25); border-radius: 14px; padding: 20px 24px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; }
.hero-inner { display: flex; justify-content: space-between; align-items: center; width: 100%; gap: 12px; }
.hero-tag { color: #818cf8; font-size: 12px; letter-spacing: 1px; }
h1 { color: #e8ebff; font-size: 22px; margin: 4px 0; }
.hero-desc { color: #94a3b8; font-size: 13px; margin: 0; }
.hero-btn { background: rgba(99,102,241,0.2); color: #a5b4fc; border: 1px solid rgba(99,102,241,0.4); border-radius: 10px; padding: 8px 16px; cursor: pointer; font-size: 13px; }
.hero-btn:hover { background: rgba(99,102,241,0.35); }
.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 12px; margin-bottom: 16px; }
.stat-card { background: rgba(15,20,40,0.5); border: 1px solid rgba(148,163,184,0.15); border-radius: 12px; padding: 14px 16px; }
.stat-label { color: #94a3b8; font-size: 12px; margin-bottom: 6px; }
.stat-big { color: #e8ebff; font-size: 22px; font-weight: 700; }
.stat-sub { color: #64748b; font-size: 11px; margin-top: 4px; }
.stat-row { display: flex; gap: 10px; font-size: 15px; font-weight: 600; }
.s-up { color: #f87171; }
.s-down { color: #34d399; }
.s-flat { color: #94a3b8; }
.temp-badge { font-size: 20px; font-weight: 700; padding: 2px 12px; border-radius: 10px; }
.temp-hot { background: rgba(244,63,94,0.18); color: #fb7185; }
.temp-neutral { background: rgba(251,191,36,0.15); color: #fbbf24; }
.temp-cold { background: rgba(56,189,248,0.15); color: #38bdf8; }
.temp-detail { display: block; color: #94a3b8; font-size: 12px; margin-top: 6px; }
.bench-5d { display: flex; flex-wrap: wrap; gap: 6px; }
.d5-item { font-size: 12px; padding: 2px 8px; border-radius: 8px; background: rgba(148,163,184,0.1); }
.profit { color: #f87171; }
.loss { color: #34d399; }
.card { background: rgba(15,20,40,0.5); border: 1px solid rgba(148,163,184,0.15); border-radius: 12px; padding: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.card-header h3 { color: #e2e8f0; font-size: 15px; margin: 0; }
.badge { font-size: 12px; padding: 2px 10px; border-radius: 10px; }
.badge.neutral { background: rgba(251,191,36,0.15); color: #fbbf24; }
.chart-container { width: 100%; height: 380px; }
</style>
