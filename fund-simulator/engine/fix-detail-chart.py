# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue'
with io.open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# 替换 initDetailChart 主体：净值折线（最近 120 交易日）+ 买卖点
old = """// 收益走势折线图（以首笔买入确认日净值为 0 基准；买入▲绿/卖出▼红标记在曲线上，悬浮显示详情）
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
}"""
new = """// 净值走势折线图（最近 120 交易日，圆润曲线；买入▲绿/卖出▼红标记在曲线上，悬浮显示买卖详情）
const initDetailChart = () => {
  const chartDom = document.getElementById('detailChart')
  if (!chartDom) return
  const existing = echarts.getInstanceByDom(chartDom)
  if (existing) existing.dispose()
  const navList = detailNavList.value
  const txs = detailTxs.value
  if (!navList.length || !txs.length) return

  // 最近 120 个交易日净值（升序）
  const recent = navList.slice(-120)
  const dates = recent.map((n: any) => n.date)
  const navs = recent.map((n: any) => n.nav)
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
      coord: [day, navs[i]],
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
        return `${p.axisValue}<br/>净值 ¥${v.toFixed(4)}`
      }
    },
    grid: { left: 54, right: 18, top: 32, bottom: 30 },
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
      scale: true,
      axisLabel: { color: '#8b92b8', fontSize: 11, formatter: '{value}' },
      splitLine: { lineStyle: { color: '#232b55' } }
    },
    series: [{
      name: '单位净值',
      type: 'line',
      smooth: true,
      symbol: 'none',
      data: navs,
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
}"""
assert old in c, 'initDetailChart block not found'
c = c.replace(old, new, 1)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c)
print('OK 净值折线 + 买卖点')
