# -*- coding: utf-8 -*-
"""Portfolio.vue：①账户 vs 沪深300 累计收益对比曲线 ②收益日历（近3个月每日盈亏热力）"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Portfolio.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) refs
old1 = """const dailyPnl = ref([]) // 每日收益明细"""
new1 = """const dailyPnl = ref([]) // 每日收益明细
const vsBench = ref(null) // 账户 vs 沪深300"""
assert s.count(old1) == 1, 'block1 not found'
s = s.replace(old1, new1)

# 2) 加载对比数据（在 dailyPnl 加载后）
old2 = """      if (dpRes.data && dpRes.data.list) {
        dailyPnl.value = dpRes.data.list
        fundNames.value = dpRes.data.fund_names || {}
      }
    } catch (e) {
      console.error('加载每日收益明细失败:', e)
    }"""
new2 = """      if (dpRes.data && dpRes.data.list) {
        dailyPnl.value = dpRes.data.list
        fundNames.value = dpRes.data.fund_names || {}
      }
    } catch (e) {
      console.error('加载每日收益明细失败:', e)
    }
    // 账户 vs 沪深300 累计收益
    try {
      const vbRes = await axios.get('/api/ai/performance-vs-benchmark')
      vsBench.value = vbRes.data || null
    } catch (e) { vsBench.value = null }
    setTimeout(() => { initVsBenchChart(); initPnlCalendar(); }, 200)"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

# 3) 渲染函数（加在 initAllocationChart 前）
old3 = """// 初始化资产配置图（真实持仓数据）
const initAllocationChart = () => {"""
new3 = """// 账户累计收益率 vs 沪深300 对比曲线（从账户有数据的日期起）
const initVsBenchChart = () => {
  const dom = document.getElementById('vsBenchChart')
  if (!dom || !vsBench.value || !vsBench.value.series.length) return
  const pts = vsBench.value.series.filter(x => x.account_pct != null || x.bench_pct != null)
  const first = pts.findIndex(x => x.account_pct != null)
  const start = first >= 0 ? first : 0
  const data = pts.slice(start)
  const chart = echarts.init(dom)
  chart.setOption({
    backgroundColor: 'transparent',
    grid: { left: 55, right: 20, top: 36, bottom: 30 },
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(15,20,40,0.95)', borderColor: 'rgba(99,102,241,0.4)', textStyle: { color: '#e2e8f0', fontSize: 12 }, valueFormatter: v => (v == null ? '—' : v + '%') },
    legend: { top: 0, textStyle: { color: '#94a3b8', fontSize: 12 }, data: ['AI账户', '沪深300'] },
    xAxis: { type: 'category', data: data.map(x => x.date), axisLine: { lineStyle: { color: 'rgba(148,163,184,0.3)' } }, axisLabel: { color: '#94a3b8', fontSize: 11, hideOverlap: true } },
    yAxis: { type: 'value', name: '累计收益%', nameTextStyle: { color: '#94a3b8' }, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.12)' } }, axisLabel: { color: '#94a3b8', formatter: '{value}%' } },
    series: [
      { name: 'AI账户', type: 'line', smooth: true, symbol: 'circle', symbolSize: 5, lineStyle: { color: '#34d399', width: 2 }, itemStyle: { color: '#34d399' }, connectNulls: true, data: data.map(x => x.account_pct), areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(52,211,153,0.25)' }, { offset: 1, color: 'rgba(52,211,153,0.02)' }]) } },
      { name: '沪深300', type: 'line', smooth: true, symbol: 'none', lineStyle: { color: '#fbbf24', width: 1.5, type: 'dashed' }, data: data.map(x => x.bench_pct) }
    ]
  })
}

// 收益日历：近3个月每日盈亏热力（盈利绿/亏损红/无数据灰）
const initPnlCalendar = () => {
  const dom = document.getElementById('pnlCalendar')
  if (!dom) return
  if (!dailyPnl.value.length) {
    dom.innerHTML = '<div style="color:#64748b;font-size:13px;padding:10px">暂无收益数据</div>'
    return
  }
  const now = new Date()
  const months = []
  for (let m = 2; m >= 0; m--) {
    const d = new Date(now.getFullYear(), now.getMonth() - m, 1)
    months.push({ y: d.getFullYear(), m: d.getMonth() })
  }
  const pnlMap = {}
  dailyPnl.value.forEach(r => { pnlMap[r.date] = r.pnl })
  let html = ''
  months.forEach(({ y, m }) => {
    const first = new Date(y, m, 1)
    const daysInMonth = new Date(y, m + 1, 0).getDate()
    const firstWeekday = first.getDay() // 0=周日
    html += '<div class="cal-month"><div class="cal-title">' + y + '年' + (m + 1) + '月</div><div class="cal-grid">'
    for (let i = 0; i < firstWeekday; i++) html += '<div class="cal-cell cal-empty"></div>'
    for (let d = 1; d <= daysInMonth; d++) {
      const ds = y + '-' + String(m + 1).padStart(2, '0') + '-' + String(d).padStart(2, '0')
      const pnl = pnlMap[ds]
      const cls = pnl == null ? 'cal-none' : (pnl > 0.005 ? 'cal-up' : pnl < -0.005 ? 'cal-down' : 'cal-flat')
      const v = pnl == null ? '' : (pnl > 0 ? '+' : '') + pnl.toFixed(0)
      html += '<div class="cal-cell ' + cls + '" title="' + ds + (pnl == null ? '' : ' 盈亏 ¥' + pnl.toFixed(2)) + '"><span class="cal-day">' + d + '</span><span class="cal-val">' + v + '</span></div>'
    }
    html += '</div></div>'
  })
  html += '<div class="cal-legend"><span class="lg lg-up">盈利</span><span class="lg lg-down">亏损</span><span class="lg lg-flat">持平</span><span class="lg lg-none">无数据</span></div>'
  dom.innerHTML = html
}

// 初始化资产配置图（真实持仓数据）
const initAllocationChart = () => {"""
assert s.count(old3) == 1, 'block3 not found'
s = s.replace(old3, new3)

# 4) 模板：每日收益明细前加对比曲线 + 收益日历
old4 = """    <!-- 每日收益明细（账户级跨基金按日贡献） -->"""
new4 = """    <!-- 账户 vs 沪深300 -->
    <a-card :bordered="false" style="margin-top:20px" v-if="vsBench">
      <div class="card-header">
        <span class="block-title-no-margin">📊 账户累计收益 vs 沪深300</span>
        <a-tag>绿色=AI账户 · 黄色虚线=沪深300（指数基准）</a-tag>
      </div>
      <div id="vsBenchChart" class="chart-container"></div>
    </a-card>

    <!-- 收益日历（近3个月） -->
    <a-card :bordered="false" style="margin-top:20px">
      <div class="card-header">
        <span class="block-title-no-margin">🗓 收益日历（近3个月）</span>
        <a-tag>每日实际盈亏，红涨绿跌（支付宝收益日历样式）</a-tag>
      </div>
      <div id="pnlCalendar"></div>
    </a-card>

    <!-- 每日收益明细（账户级跨基金按日贡献） -->"""
assert s.count(old4) == 1, 'block4 not found'
s = s.replace(old4, new4)

# 5) 样式
old5 = """.chart-container {
  height: 350px;
  width: 100%;
}"""
new5 = """.chart-container {
  height: 350px;
  width: 100%;
}

/* 收益日历 */
#pnlCalendar { padding: 8px 0; }
.cal-month { margin-bottom: 16px; }
.cal-title { color: #94a3b8; font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }
.cal-cell { aspect-ratio: 1; border-radius: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 11px; min-height: 44px; }
.cal-day { color: #cbd5e1; font-size: 11px; }
.cal-val { font-size: 10px; font-weight: 600; margin-top: 1px; }
.cal-up { background: rgba(52,211,153,0.22); }
.cal-up .cal-val { color: #34d399; }
.cal-down { background: rgba(248,113,113,0.22); }
.cal-down .cal-val { color: #f87171; }
.cal-flat { background: rgba(148,163,184,0.15); }
.cal-flat .cal-val { color: #94a3b8; }
.cal-none { background: rgba(148,163,184,0.06); }
.cal-empty { background: transparent; }
.cal-legend { display: flex; gap: 12px; justify-content: flex-end; font-size: 11px; color: #94a3b8; padding-top: 6px; }
.lg { display: inline-flex; align-items: center; gap: 4px; }
.lg::before { content: ''; width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
.lg-up::before { background: rgba(52,211,153,0.6); }
.lg-down::before { background: rgba(248,113,113,0.6); }
.lg-flat::before { background: rgba(148,163,184,0.5); }
.lg-none::before { background: rgba(148,163,184,0.12); }"""
assert s.count(old5) == 1, 'block5 not found'
s = s.replace(old5, new5)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Portfolio vs-bench + calendar patched')
