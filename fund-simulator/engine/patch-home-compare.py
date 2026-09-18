# -*- coding: utf-8 -*-
"""Home.vue：新增「🤝 双 AI 基金经理经营对比」卡（并排指标 + 每日资产双线图）"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) ref
old1 = """const hotspots = ref<any>(null) // AI 市场热点分析"""
new1 = """const hotspots = ref<any>(null) // AI 市场热点分析
const aiCompare = ref<any>(null) // 双经理经营对比"""
assert s.count(old1) == 1, 'block1 not found'
s = s.replace(old1, new1)

# 2) 加载对比（热点加载后）
old2 = """      // AI 市场热点
      try {
        const hpRes = await axios.get('/api/ai/hotspots')
        hotspots.value = hpRes.data || null
      } catch (e5) { hotspots.value = null }"""
new2 = """      // AI 市场热点
      try {
        const hpRes = await axios.get('/api/ai/hotspots')
        hotspots.value = hpRes.data || null
      } catch (e5) { hotspots.value = null }
      // 双经理经营对比
      try {
        const cpRes = await axios.get('/api/ai/compare')
        aiCompare.value = cpRes.data || null
      } catch (e6) { aiCompare.value = null }
      setTimeout(() => initCompareChart(), 300)"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

# 3) 对比图渲染函数（加在 hotspotBadge 前）
old3 = """// 热点状态徽章样式"""
new3 = """// 双经理每日资产对比图
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
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(15,20,40,0.95)', borderColor: 'rgba(99,102,241,0.4)', textStyle: { color: '#e2e8f0', fontSize: 12 }, valueFormatter: v => (v == null ? '—' : '¥' + Number(v).toLocaleString()) },
    legend: { top: 0, textStyle: { color: '#94a3b8', fontSize: 12 }, data: [u0.name, u1.name] },
    xAxis: { type: 'category', data: daily.map(d => d.date), axisLine: { lineStyle: { color: 'rgba(148,163,184,0.3)' } }, axisLabel: { color: '#94a3b8', fontSize: 11, hideOverlap: true } },
    yAxis: { type: 'value', name: '总资产', nameTextStyle: { color: '#94a3b8' }, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.12)' } }, axisLabel: { color: '#94a3b8', formatter: v => (v / 10000).toFixed(1) + '万' } },
    series: [
      { name: u0.name, type: 'line', smooth: true, symbol: 'circle', symbolSize: 5, lineStyle: { color: '#34d399', width: 2 }, itemStyle: { color: '#34d399' }, data: daily.map(d => d[u0.id]) },
      { name: u1.name, type: 'line', smooth: true, symbol: 'circle', symbolSize: 5, lineStyle: { color: '#fbbf24', width: 2 }, itemStyle: { color: '#fbbf24' }, data: daily.map(d => d[u1.id]) }
    ]
  })
}

// 热点状态徽章样式"""
assert s.count(old3) == 1, 'block3 not found'
s = s.replace(old3, new3)

# 4) 模板：热点卡后加对比卡
old4 = """    <!-- AI 决策轨迹 -->"""
new4 = """    <!-- 双经理经营对比 -->
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

    <!-- AI 决策轨迹 -->"""
assert s.count(old4) == 1, 'block4 not found'
s = s.replace(old4, new4)

# 5) 样式
old5 = """.hotspot-cold { background: rgba(100,116,139,0.2); color: #94a3b8; }"""
new5 = """.hotspot-cold { background: rgba(100,116,139,0.2); color: #94a3b8; }
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
.muted { color: #64748b; font-size: 12px; font-weight: 400; }"""
assert s.count(old5) == 1, 'block5 not found'
s = s.replace(old5, new5)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Home compare card patched')
