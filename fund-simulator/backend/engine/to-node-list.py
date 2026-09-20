# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue'
c = io.open(p, encoding='utf-8').read()

# ========== 1. script：detailNavList + viewFundDetail(图表版) → detailNavMap(增长率) + 节点版 ==========
old1 = """const detailTxs = ref<any[]>([])
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

// 净值走势折线图（最近 120 交易日，圆润曲线；买入▲绿/卖出▼红标记在曲线上，悬浮显示买卖详情）
const initDetailChart = () => {
  const chartDom = document.getElementById('detailChart')
  if (!chartDom) return
  const existing = echarts.getInstanceByDom(chartDom)
  if (existing) existing.dispose()
  const navList = detailNavList.value
  const txs = detailTxs.value
  if (!navList.length || !txs.length) return

  // 最近 120 个交易日净值（升序）→ 涨幅%（以区间起点净值为 0 基准）
  const recent = navList.slice(-120)
  const dates = recent.map((n: any) => n.date)
  const navs = recent.map((n: any) => n.nav)
  const baseNav = navs[0] || 1
  const rets = navs.map((v: number) => (v / baseNav - 1) * 100)
  const dateIdx = new Map(dates.map((d: any, i: number) => [d, i]))

  // 买卖节点（定位到当日净值；交易日期斜杠转横线归一化）
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
      symbolSize: 18,
      itemStyle: { color: isBuy ? '#34d399' : '#f87171', borderColor: '#0d1330', borderWidth: 2 },
      label: { show: true, formatter: isBuy ? '买' : '卖', fontSize: 12, fontWeight: 700, color: '#ffffff' },
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
        if (!p || p.axisValue == null) return ''
        const v = Number(p.value)
        return `${p.axisValue}<br/>涨幅 ${v >= 0 ? '+' : ''}${v.toFixed(2)}%`
      }
    },
    grid: { left: 54, right: 18, top: 32, bottom: 30 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLine: { lineStyle: { color: '#2c3466' } },
      axisLabel: { color: '#8b92b8', fontSize: 11, interval: (idx: number) => idx === 0 || idx === dates.length - 1 || idx % Math.max(1, Math.floor(dates.length / 8)) === 0 },
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
            return `${d._action} · ${d._date}<br/>份额 ${d._shares.toLocaleString()} 份<br/>净值 ¥${d._price.toFixed(4)} · 手续费 ¥${d._fees.toFixed(2)}`
          }
        }
      }
    }]
  })
  window.addEventListener('resize', () => myChart.resize())
}
"""
new1 = """const detailTxs = ref<any[]>([])
const detailNavMap = ref<Record<string, number>>({}) // date(YYYY-MM-DD) → 日增长率

// 该交易日增长率（交易日期 2026/09/16 斜杠 → 归一化匹配净值日期 2026-09-16）
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

// 查看基金详情（弹窗：操作节点列表（图标+增长率+悬浮明细） + 基金信息）
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
    // 净值历史（含日增长率，按日期匹配节点增长率）
    const navRes = await axios.get(`/api/funds/${code}/nav`, { params: { limit: 300 } })
    const navRows = Array.isArray(navRes.data) ? navRes.data : []
    const map: Record<string, number> = {}
    for (const n of navRows) {
      if (n.nav_date && n.daily_return != null) map[n.nav_date] = n.daily_return
    }
    detailNavMap.value = map
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
  }
}
"""
assert old1 in c, 'anchor1 not found'
c = c.replace(old1, new1, 1)

# ========== 2. 模板：图表 → 节点列表 ==========
old2 = """          <div class="detail-section-title">涨幅</div>
          <div v-if="detailTxs.length === 0" class="empty-state">
            <div class="empty-icon">📝</div>
            <p>暂无该基金操作记录</p>
          </div>
          <div v-else id="detailChart" class="detail-chart"></div>
"""
new2 = """          <div class="detail-section-title">操作记录</div>
          <div v-if="detailTxs.length === 0" class="empty-state">
            <div class="empty-icon">📝</div>
            <p>暂无该基金操作记录</p>
          </div>
          <div v-else class="tx-node-list">
            <a-tooltip
              v-for="(tx, i) in detailTxs"
              :key="i"
              :title="`份额 ${(tx.shares || 0).toLocaleString()} 份 · 净值 ¥${(tx.price || 0).toFixed(4)} · 手续费 ¥${(tx.fees || 0).toFixed(2)}`"
              placement="left"
            >
              <div class="tx-node-row">
                <span class="tx-node-icon" :class="tx.action === '买入' ? 'buy' : 'sell'">{{ tx.action === '买入' ? '▲' : '▼' }}</span>
                <div class="tx-node-body">
                  <div class="tx-node-top">
                    <span class="tx-growth" :class="growthCls(tx)">{{ growthText(tx) }}</span>
                    <span class="tx-tag" :class="tx.action === '买入' ? 'buy' : 'sell'">{{ tx.action }}</span>
                    <span class="tx-date">{{ tx.date }}</span>
                  </div>
                  <div class="tx-node-sub">
                    <span class="tx-amount">¥{{ (tx.amount || 0).toFixed(2) }}</span>
                    <span class="tx-fee" v-if="(tx.fees || 0) > 0">手续费 ¥{{ tx.fees.toFixed(2) }}</span>
                  </div>
                </div>
              </div>
            </a-tooltip>
          </div>
"""
assert old2 in c, 'anchor2 not found'
c = c.replace(old2, new2, 1)

# ========== 3. CSS：节点列表样式（替换 .detail-chart） ==========
old3 = """.detail-chart {
  height: 280px;
  width: 100%;
  margin: 4px 0 8px;
}
"""
new3 = """.tx-node-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 2px 0 6px;
}
.tx-node-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(44, 52, 102, 0.6);
  border-radius: 10px;
  transition: border-color 0.2s, background 0.2s;
}
.tx-node-row:hover {
  border-color: #4c5690;
  background: rgba(255, 255, 255, 0.07);
}
.tx-node-icon {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: #ffffff;
  flex-shrink: 0;
}
.tx-node-icon.buy {
  background: linear-gradient(135deg, #10b981, #34d399);
  box-shadow: 0 2px 8px rgba(52, 211, 153, 0.35);
}
.tx-node-icon.sell {
  background: linear-gradient(135deg, #ef4444, #f87171);
  box-shadow: 0 2px 8px rgba(248, 113, 113, 0.35);
}
.tx-node-body {
  flex: 1;
  min-width: 0;
}
.tx-node-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}
.tx-growth {
  font-size: 13px;
  font-weight: 600;
  min-width: 62px;
}
.tx-tag {
  font-size: 12px;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 4px;
}
.tx-tag.buy {
  color: #34d399;
  background: rgba(52, 211, 153, 0.12);
}
.tx-tag.sell {
  color: #f87171;
  background: rgba(248, 113, 113, 0.12);
}
.tx-date {
  color: #8b92b8;
  font-size: 12px;
}
.tx-node-sub {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 13px;
  color: #c8cdf2;
}
.tx-amount {
  font-weight: 600;
  color: #e8ebff;
}
.tx-fee {
  font-size: 12px;
  color: #8b92b8;
}
"""
assert old3 in c, 'anchor3 not found'
c = c.replace(old3, new3, 1)

io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK 节点列表版弹窗')
