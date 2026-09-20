# -*- coding: utf-8 -*-
"""App.vue：①顶栏加“市场行情”菜单 ②activeIndex 匹配 /market"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\App.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old1 = """            <a-menu-item key="/funds">
              <UnorderedListOutlined />
              <span>基金库</span>
            </a-menu-item>"""
new1 = """            <a-menu-item key="/funds">
              <UnorderedListOutlined />
              <span>基金库</span>
            </a-menu-item>
            <a-menu-item key="/market">
              <LineChartOutlined />
              <span>市场行情</span>
            </a-menu-item>"""
assert s.count(old1) == 1, 'menu not found'
s = s.replace(old1, new1)

old2 = """  if (p.startsWith('/funds')) return '/funds'
  if (p.startsWith('/analysis') || p.startsWith('/ai-analysis')) return '/analysis'"""
new2 = """  if (p.startsWith('/funds')) return '/funds'
  if (p.startsWith('/market')) return '/market'
  if (p.startsWith('/analysis') || p.startsWith('/ai-analysis')) return '/analysis'"""
assert s.count(old2) == 1, 'activeIndex not found'
s = s.replace(old2, new2)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('App.vue market menu added')
