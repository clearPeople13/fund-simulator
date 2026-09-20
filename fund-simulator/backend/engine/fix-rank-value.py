# -*- coding: utf-8 -*-
"""修复 rankValue：后端 r6m 别名 recent_return，主列取不到 r6m 显示 —"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Funds.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """// 当前维度值（scale 显示规模，其余为涨幅）
const rankValue = (record) => {
  const v = record[sortKey.value]
  return v != null ? v : null
}"""
new = """// 当前维度值（scale 显示规模，其余为涨幅；后端 r6m 返回为 recent_return 别名）
const rankValue = (record) => {
  const key = sortKey.value === 'r6m' ? 'recent_return' : sortKey.value
  const v = record[key]
  return v != null ? v : null
}"""
assert s.count(old) == 1, 'block not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('rankValue fixed')
