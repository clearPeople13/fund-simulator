# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue'
with io.open(p, 'r', encoding='utf-8') as f:
    c = f.read()

old = """  const myChart = echarts.init(chartDom)
  myChart.setOption({"""
new = """  console.log('[DETAIL_CHART] marks=', JSON.stringify(marks.map((m: any) => ({ n: m.name, c: m.coord }))), 'dates=', dates.length, 'first=', dates[0], 'last=', dates[dates.length - 1])
  const myChart = echarts.init(chartDom)
  myChart.setOption({"""
assert old in c, 'anchor'
c = c.replace(old, new, 1)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c)
print('OK debug log added')
