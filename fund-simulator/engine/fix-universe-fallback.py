# -*- coding: utf-8 -*-
"""Analysis/Portfolio 市值口径统一：优先用后端 holdings.market_value（fund_nav 最新净值），不因 universe top100 缺失回退成本价"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views"

# ---- Portfolio.vue ----
p = os.path.join(BASE, 'Portfolio.vue')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()
old = """    for (const [code, h] of Object.entries(pf.holdings || {})) {
      const fund = fundMap[code] || {}
      const currentPrice = fund.latest_nav != null ? fund.latest_nav : h.cost
      const marketValue = h.shares * currentPrice
      const profit = marketValue - h.total_cost"""
new = """    for (const [code, h] of Object.entries(pf.holdings || {})) {
      const fund = fundMap[code] || {}
      // 市值优先用后端持仓 market_value（fund_nav 最新净值口径）；fundMap 仅 universe top100，持仓基金可能不在其中
      const marketValue = h.market_value != null ? h.market_value : (h.shares * (fund.latest_nav != null ? fund.latest_nav : h.cost))
      const currentPrice = marketValue / h.shares
      const profit = marketValue - h.total_cost"""
assert s.count(old) == 1, 'Portfolio.vue block not found'
s = s.replace(old, new)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Portfolio.vue patched')

# ---- Analysis.vue ----
p = os.path.join(BASE, 'Analysis.vue')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()
old2 = """    for (const [code, h] of Object.entries(pf.holdings || {})) {
      const fund = fundMap[code] || {}
      const price = fund.latest_nav != null ? fund.latest_nav : h.cost
      mvs[code] = h.shares * price
      totalMv += mvs[code]
    }"""
new2 = """    for (const [code, h] of Object.entries(pf.holdings || {})) {
      const fund = fundMap[code] || {}
      // 市值优先用后端持仓 market_value（fund_nav 最新净值口径）；fundMap 仅 universe top100，持仓基金可能不在其中
      mvs[code] = h.market_value != null ? h.market_value : (h.shares * (fund.latest_nav != null ? fund.latest_nav : h.cost))
      totalMv += mvs[code]
    }"""
assert s.count(old2) == 1, 'Analysis.vue block not found'
s = s.replace(old2, new2)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Analysis.vue patched')
