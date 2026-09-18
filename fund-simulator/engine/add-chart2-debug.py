# -*- coding: utf-8 -*-
import io
p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue'
c = io.open(p, encoding='utf-8').read()
anchor = """  const myChart = echarts.init(chartDom)
  myChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 20, 48, 0.92)',"""
assert c.count(anchor) == 1, 'anchor count=%d' % c.count(anchor)
log = "  console.log('[CHART2] marks=', JSON.stringify(marks.map((m: any) => ({ n: m.name, c: m.coord, p: m._pending }))), 'dates=', sDates.length, 'last=', sDates[sDates.length - 1])\n" + anchor
c = c.replace(anchor, log, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
