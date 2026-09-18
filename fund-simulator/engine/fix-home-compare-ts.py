# -*- coding: utf-8 -*-
"""Home.vue 对比图 TS 参数类型修复"""
import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()
s = s.replace('valueFormatter: v => (v == null ?', 'valueFormatter: (v: any) => (v == null ?')
s = s.replace('data: daily.map(d => d.date)', 'data: daily.map((d: any) => d.date)')
s = s.replace('axisLabel: { color: \'#94a3b8\', formatter: v => (v / 10000).toFixed(1) + \'万\' }', 'axisLabel: { color: \'#94a3b8\', formatter: (v: any) => (v / 10000).toFixed(1) + \'万\' }')
s = s.replace('data: daily.map(d => d[u0.id])', 'data: daily.map((d: any) => d[u0.id])')
s = s.replace('data: daily.map(d => d[u1.id])', 'data: daily.map((d: any) => d[u1.id])')
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('ts types fixed')
