# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue'
c = io.open(p, encoding='utf-8').read()

# 1. 标题：收益走势 → 涨幅
old_t = """          <div class="detail-section-title">收益走势</div>"""
new_t = """          <div class="detail-section-title">涨幅</div>"""
assert old_t in c, 'title anchor'
c = c.replace(old_t, new_t, 1)

# 2. 折线数据：净值 → 区间累计涨幅%（以最近 120 条起点为 0 基准）
old_d = """  // 最近 120 个交易日净值（升序）
  const recent = navList.slice(-120)
  const dates = recent.map((n: any) => n.date)
  const navs = recent.map((n: any) => n.nav)
  const dateIdx = new Map(dates.map((d: any, i: number) => [d, i]))"""
new_d = """  // 最近 120 个交易日净值（升序）→ 涨幅%（以区间起点净值为 0 基准）
  const recent = navList.slice(-120)
  const dates = recent.map((n: any) => n.date)
  const navs = recent.map((n: any) => n.nav)
  const baseNav = navs[0] || 1
  const rets = navs.map((v: number) => (v / baseNav - 1) * 100)
  const dateIdx = new Map(dates.map((d: any, i: number) => [d, i]))"""
assert old_d in c, 'data anchor'
c = c.replace(old_d, new_d, 1)

# 3. markPoint 坐标用涨幅
old_m = """      coord: [day, navs[i]],"""
new_m = """      coord: [day, rets[i]],"""
assert old_m in c, 'mark anchor'
c = c.replace(old_m, new_m, 1)

# 4. y 轴 % + series 数据/名称
old_y = """    yAxis: {
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
      data: navs,"""
new_y = """    yAxis: {
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
      data: rets,"""
assert old_y in c, 'yaxis anchor'
c = c.replace(old_y, new_y, 1)

# 5. 折线 tooltip：净值 → 涨幅
old_tt = """        if (!p || p.axisValue == null) return ''
        const v = Number(p.value)
        return `${p.axisValue}<br/>净值 ¥${v.toFixed(4)}`"""
new_tt = """        if (!p || p.axisValue == null) return ''
        const v = Number(p.value)
        return `${p.axisValue}<br/>涨幅 ${v >= 0 ? '+' : ''}${v.toFixed(2)}%`"""
assert old_tt in c, 'tooltip anchor'
c = c.replace(old_tt, new_tt, 1)

io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK 涨幅折线图')
