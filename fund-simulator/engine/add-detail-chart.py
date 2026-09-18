# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue'
with io.open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# ========== 1. script：detailNavMap + growth 函数 → detailNavList ==========
old1 = """const detailTxs = ref<any[]>([])
const detailNavMap = ref<Record<string, number>>({})

// 该交易日增长率（按交易日期匹配净值历史；交易日期为 2026/09/16，净值日期为 2026-09-16，需归一化）
const growthOf = (tx: any): number | null => {
  const day = String(tx.date).slice(0, 10).replace(/\\//g, '-')
  const g = detailNavMap.value[day]
  return g !== undefined && g !== null ? g : null
}
// 增长率文本（含符号），无数据返回 —
const growthText = (tx: any): string => {
  const g = growthOf(tx)
  return g != null ? (g >= 0 ? '+' : '') + g.toFixed(2) + '%' : '—'
}
// 增长率颜色
const growthCls = (tx: any): string => {
  const g = growthOf(tx)
  return g != null && g >= 0 ? 'profit' : 'loss'
}
"""
new1 = """const detailTxs = ref<any[]>([])
const detailNavList = ref<any[]>([]) // 升序 [{date, nav}]

// 查看基金详情（弹窗：收益走势折线图 + 买卖节点 + 基金信息，真实数据）
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
    // 净值历史（接口倒序，转升序存 unit_nav 供收益率曲线）
    const navRes = await axios.get(`/api/funds/${code}/nav`, { params: { limit: 300 } })
    const navRows = Array.isArray(navRes.data) ? navRes.data : []
    detailNavList.value = navRows
      .map((n: any) => ({ date: n.nav_date, nav: n.unit_nav }))
      .filter((n: any) => n.date && n.nav != null)
      .reverse()
    // 基金基本信息
    const fundRes = await axios.get('/api/funds', { params: { limit: 100 } })
    const info = ((fundRes.data && fundRes.data.data) || []).find((f: any) => f.fund_code === code)
    if (info) {
      detailFund.value = {
        code: info.fund_code,
        name: info.fund_name,
        type: info.fund_type,
        manager: info.manager,
        inception_date: info.inception_date,
        benchmark: info.benchmark
      }
    }
  } catch (error) {
    console.error('加载基金详情失败:', error)
  } finally {
    detailLoading.value = false
    setTimeout(() => initDetailChart(), 120)
  }
}

// 收益走势折线图（以首笔买入确认日净值为 0 基准；买入▲绿/卖出▼红标记在曲线上，悬浮显示详情）
const initDetailChart = () => {
  const chartDom = document.getElementById('detailChart')
  if (!chartDom) return
  const existing = echarts.getInstanceByDom(chartDom)
  if (existing) existing.dispose()
  const navList = detailNavList.value
  const txs = detailTxs.value
  if (!navList.length || !txs.length) return

  // 基准日：首笔买入确认日；基准净值 = 当日单位净值（兜底取首条）
  const firstBuy = txs.find((t: any) => t.action === '买入')
  const baseDay = firstBuy ? String(firstBuy.date).slice(0, 10).replace(/\\//g, '-') : navList[0].date
  let baseNav = navList.find((n: any) => n.date === baseDay)?.nav
  if (baseNav == null) baseNav = navList[0].nav
  const startIdx = Math.max(0, navList.findIndex((n: any) => n.date === baseDay))

  const dates = navList.slice(startIdx).map((n: any) => n.date)
  const rets = navList.slice(startIdx).map((n: any) => (n.nav / baseNav - 1) * 100)
  const dateIdx = new Map(dates.map((d: any, i: number) => [d, i]))

  // 买卖节点
  const marks: any[] = []
  for (const tx of txs) {
    const day = String(tx.date).slice(0, 10).replace(/\\//g, '-')
    const i = dateIdx.get(day)
    if (i == null) continue
    const isBuy = tx.action === '买入'
    marks.push({
      name: isBuy ? '买入' : '卖出',
      coord: [day, rets[i]],
      symbol: 'triangle',
      symbolRotate: isBuy ? 0 : 180,
      symbolSize: 13,
      itemStyle: { color: isBuy ? '#34d399' : '#f87171', borderColor: '#0d1330', borderWidth: 1.5 },
      label: { show: true, formatter: isBuy ? '买' : '卖', fontSize: 9, color: '#ffffff' },
      _action: isBuy ? '买入' : '卖出',
      _date: tx.date,
      _shares: Number(tx.shares) || 0,
      _price: Number(tx.price) || 0,
      _fees: Number(tx.fees) || 0
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
        if (p && p.componentType === 'markPoint' && p.data) {
          const d = p.data
          return `${d._action} · ${d._date}<br/>份额 ${d._shares.toLocaleString()} 份<br/>净值 ¥${d._price.toFixed(4)} · 手续费 ¥${d._fees.toFixed(2)}`
        }
        if (!p || p.axisValue == null) return ''
        const v = Number(p.value)
        return `${p.axisValue}<br/>收益率 ${v >= 0 ? '+' : ''}${v.toFixed(2)}%`
      }
    },
    grid: { left: 46, right: 18, top: 32, bottom: 30 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLine: { lineStyle: { color: '#2c3466' } },
      axisLabel: { color: '#8b92b8', fontSize: 11, interval: Math.max(0, Math.floor(dates.length / 8) - 1) },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#8b92b8', fontSize: 11, formatter: '{value}%' },
      splitLine: { lineStyle: { color: '#232b55' } }
    },
    series: [{
      name: '收益率',
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
        symbolOffset: [0, -8],
        data: marks
      }
    }]
  })
  window.addEventListener('resize', () => myChart.resize())
}
"""
assert old1 in c, 'anchor1 not found'
c = c.replace(old1, new1, 1)

# ========== 2. 模板：时间线 → 折线图 ==========
old2 = """          <div class="detail-section-title">操作记录</div>
          <div v-if="detailTxs.length === 0" class="empty-state">
            <div class="empty-icon">📝</div>
            <p>暂无该基金操作记录</p>
          </div>
          <a-timeline v-else class="detail-timeline">
            <a-timeline-item
              v-for="(tx, i) in detailTxs"
              :key="i"
              :color="tx.action === '买入' ? '#34d399' : '#f87171'"
            >
              <a-tooltip
                :title="`份额 ${tx.shares.toLocaleString()} 份 · 净值 ¥${tx.price.toFixed(4)} · 手续费 ¥${tx.fees.toFixed(2)}`"
                placement="right"
              >
                <div class="tx-node">
                  <div class="tx-growth" :class="growthCls(tx)">
                    {{ growthText(tx) }}
                  </div>
                  <div class="tx-main">
                    <span class="tx-icon" :class="tx.action === '买入' ? 'icon-buy' : 'icon-sell'">
                      {{ tx.action === '买入' ? '▲' : '▼' }}
                    </span>
                    <span class="tx-date">{{ tx.date }}</span>
                    <span class="tx-action" :class="tx.action === '买入' ? 'tag-buy' : 'tag-sell'">{{ tx.action }}</span>
                    <span class="tx-amount">¥{{ tx.amount.toFixed(2) }}</span>
                    <span class="tx-fee" v-if="tx.fees > 0">手续费 ¥{{ tx.fees.toFixed(2) }}</span>
                  </div>
                </div>
              </a-tooltip>
            </a-timeline-item>
          </a-timeline>
"""
new2 = """          <div class="detail-section-title">收益走势</div>
          <div v-if="detailTxs.length === 0" class="empty-state">
            <div class="empty-icon">📝</div>
            <p>暂无该基金操作记录</p>
          </div>
          <div v-else id="detailChart" class="detail-chart"></div>
"""
assert old2 in c, 'anchor2 not found'
c = c.replace(old2, new2, 1)

# ========== 3. CSS：加折线图容器 ==========
old3 = """.detail-timeline :deep(.ant-timeline-item-tail) {
  border-left: 2px solid #2c3466;
}"""
new3 = """.detail-chart {
  height: 280px;
  width: 100%;
  margin: 4px 0 8px;
}

.detail-timeline :deep(.ant-timeline-item-tail) {
  border-left: 2px solid #2c3466;
}"""
assert old3 in c, 'anchor3 not found'
c = c.replace(old3, new3, 1)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c)
print('OK Home.vue 弹窗折线图')
