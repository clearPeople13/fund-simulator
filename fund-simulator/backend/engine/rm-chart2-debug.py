# -*- coding: utf-8 -*-
import io
p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue'
c = io.open(p, encoding='utf-8').read()
bad = "  console.log('[CHART2] marks=', JSON.stringify(marks.map((m: any) => ({ n: m.name, c: m.coord, p: m._pending }))), 'dates=', sDates.length, 'last=', sDates[sDates.length - 1])\n"
assert c.count(bad) == 1
c = c.replace(bad, '', 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
