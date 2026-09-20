# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue'
c = io.open(p, encoding='utf-8').read()

old = """      markPoint: {
        symbolOffset: [0, -12],
        data: marks
      }"""
new = """      markPoint: {
        symbolOffset: [0, -10],
        data: marks,
        tooltip: {
          formatter: (p: any) => {
            const d = p && p.data
            if (!d) return ''
            return `${d._action} · ${d._date}<br/>份额 ${d._shares.toLocaleString()} 份<br/>净值 ¥${d._price.toFixed(4)} · 手续费 ¥${d._fees.toFixed(2)}`
          }
        }
      }"""
assert old in c, 'markPoint anchor not found'
c = c.replace(old, new, 1)

# series tooltip formatter 简化（去掉 markPoint 分支，只留 axis 逻辑）
old2 = """      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params
        if (p && p.componentType === 'markPoint' && p.data) {
          const d = p.data
          return `${d._action} · ${d._date}<br/>份额 ${d._shares.toLocaleString()} 份<br/>净值 ¥${d._price.toFixed(4)} · 手续费 ¥${d._fees.toFixed(2)}`
        }
        if (!p || p.axisValue == null) return ''
        const v = Number(p.value)
        return `${p.axisValue}<br/>净值 ¥${v.toFixed(4)}`
      }"""
new2 = """      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params
        if (!p || p.axisValue == null) return ''
        const v = Number(p.value)
        return `${p.axisValue}<br/>净值 ¥${v.toFixed(4)}`
      }"""
assert old2 in c, 'tooltip formatter anchor not found'
c = c.replace(old2, new2, 1)

io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK markPoint 独立 tooltip')
