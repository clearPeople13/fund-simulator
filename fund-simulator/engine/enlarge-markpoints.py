# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue'
with io.open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. markPoint 节点放大 + 标签醒目
old1 = """      symbol: 'triangle',
      symbolRotate: isBuy ? 0 : 180,
      symbolSize: 13,
      itemStyle: { color: isBuy ? '#34d399' : '#f87171', borderColor: '#0d1330', borderWidth: 1.5 },
      label: { show: true, formatter: isBuy ? '买' : '卖', fontSize: 9, color: '#ffffff' },"""
new1 = """      symbol: 'triangle',
      symbolRotate: isBuy ? 0 : 180,
      symbolSize: 18,
      itemStyle: { color: isBuy ? '#34d399' : '#f87171', borderColor: '#0d1330', borderWidth: 2 },
      label: { show: true, formatter: isBuy ? '买' : '卖', fontSize: 12, fontWeight: 700, color: '#ffffff' },"""
assert old1 in c, 'anchor1'
c = c.replace(old1, new1, 1)

# 2. x 轴标签：保证首尾可见（interval 用函数）
old2 = """axisLabel: { color: '#8b92b8', fontSize: 11, interval: Math.max(0, Math.floor(dates.length / 8) - 1) },"""
new2 = """axisLabel: { color: '#8b92b8', fontSize: 11, interval: (idx: number) => idx === 0 || idx === dates.length - 1 || idx % Math.max(1, Math.floor(dates.length / 8)) === 0 },"""
assert old2 in c, 'anchor2'
c = c.replace(old2, new2, 1)

# 3. markPoint symbolOffset 上移一点
old3 = """markPoint: {
        symbolOffset: [0, -8],
        data: marks
      }"""
new3 = """markPoint: {
        symbolOffset: [0, -12],
        data: marks
      }"""
assert old3 in c, 'anchor3'
c = c.replace(old3, new3, 1)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c)
print('OK 节点放大')
