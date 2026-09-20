# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue'
c = io.open(p, encoding='utf-8').read()

bad = "  console.log('[DETAIL_CHART] marks=', JSON.stringify(marks.map((m: any) => ({ n: m.name, c: m.coord }))), 'dates=', dates.length, 'first=', dates[0], 'last=', dates[dates.length - 1])\n"
assert c.count(bad) == 1, 'bad log count=%d' % c.count(bad)
c = c.replace(bad, '', 1)

good_anchor = """  const myChart = echarts.init(chartDom)
  myChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 20, 48, 0.92)',"""
assert c.count(good_anchor) == 1, 'anchor count=%d' % c.count(good_anchor)
good_log = "  console.log('[DETAIL_CHART] marks=', JSON.stringify(marks.map((m: any) => ({ n: m.name, c: m.coord }))), 'dates=', dates.length, 'first=', dates[0], 'last=', dates[dates.length - 1])\n" + good_anchor
c = c.replace(good_anchor, good_log, 1)

io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK log moved to initDetailChart')
