# -*- coding: utf-8 -*-
"""/api/ai/portfolio 顶层补 realized_pnl（=Σ各持仓 realized_pnl），前端收益构成用系统账本"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """    const marketValueTotal = Object.values(holdings).reduce((sum, h) => sum + (h.market_value || h.total_cost), 0);
    res.json({
      initial_capital: portfolio.initial_capital,
      current_capital: portfolio.current_capital,
      holdings,
      total_assets: portfolio.current_capital + marketValueTotal,
      today_pnl: todayPnlRow ? todayPnlRow.daily_pnl : null,
      fee_stats: feeStats
    });"""
new = """    const marketValueTotal = Object.values(holdings).reduce((sum, h) => sum + (h.market_value || h.total_cost), 0);
    // 累计已实现盈亏 = Σ各持仓 realized_pnl（系统账本，精确对账）
    const realizedTotal = Object.values(holdings).reduce((sum, h) => sum + (h.realized_pnl || 0), 0);
    res.json({
      initial_capital: portfolio.initial_capital,
      current_capital: portfolio.current_capital,
      holdings,
      total_assets: portfolio.current_capital + marketValueTotal,
      realized_pnl: Math.round(realizedTotal * 100) / 100,
      today_pnl: todayPnlRow ? todayPnlRow.daily_pnl : null,
      fee_stats: feeStats
    });"""
assert s.count(old) == 1, 'block not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('server.js patched')
