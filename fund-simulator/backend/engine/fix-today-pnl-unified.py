# -*- coding: utf-8 -*-
"""统一今日盈亏口径：持仓明细用 份额×(今日净值-昨日净值)，与每日收益明细/账户快照一致
（原 市值×收益率 会多乘 (1+收益率) 因子，005827 显示 47.77 vs 正确 47.54）"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """        const isTodayNav = isSameLocalDay(latestNav.nav_date + " 00:00:00"); const todayPnl = pendingConfirm ? 0 : (isTodayNav ? marketValue * dailyReturn / 100 : null)"""
new = """        const isTodayNav = isSameLocalDay(latestNav.nav_date + " 00:00:00")
        // 今日盈亏统一口径：份额 × (今日净值 - 昨日净值)（与每日收益明细一致；市值×收益率会多乘(1+收益率)）
        const prevNav = navData.length >= 2 ? navData[1].unit_nav : null
        const todayPnl = pendingConfirm ? 0 : (isTodayNav && prevNav != null ? holding.shares * (currentPrice - prevNav) : null)"""
assert s.count(old) == 1, 'block not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Home.vue today_pnl unified')
