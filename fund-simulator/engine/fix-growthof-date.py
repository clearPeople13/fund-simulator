# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue'
with io.open(p, 'r', encoding='utf-8') as f:
    c = f.read()

old = """// 该交易日增长率（按交易日期匹配净值历史）
const growthOf = (tx: any): number | null => {
  const day = String(tx.date).slice(0, 10)
  const g = detailNavMap.value[day]
  return g !== undefined && g !== null ? g : null
}"""
new = """// 该交易日增长率（按交易日期匹配净值历史；交易日期为 2026/09/16，净值日期为 2026-09-16，需归一化）
const growthOf = (tx: any): number | null => {
  const day = String(tx.date).slice(0, 10).replace(/\\//g, '-')
  const g = detailNavMap.value[day]
  return g !== undefined && g !== null ? g : null
}"""
assert old in c, 'anchor not found'
c = c.replace(old, new)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c)
print('OK: growthOf 日期归一化')
