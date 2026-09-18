# -*- coding: utf-8 -*-
"""initAllocChart 改用 import 的 echarts（与 initAssetChart 一致），修复 window.echarts undefined 导致环形图不渲染"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """const initAllocChart = () => {
  const el = document.getElementById('allocChart')
  if (!el || !(window as any).echarts) return
  const chart = (window as any).echarts.getInstanceByDom(el) || (window as any).echarts.init(el)"""
new = """const initAllocChart = () => {
  const el = document.getElementById('allocChart')
  if (!el) return
  const chart = echarts.getInstanceByDom(el) || echarts.init(el)"""
assert s.count(old) == 1, 'block not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Home.vue patched')
