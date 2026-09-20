# -*- coding: utf-8 -*-
"""修复累计收益恒 0：
1) 后端 /api/ai/portfolio：holdings 附 latest_nav/market_value/daily_return，total_assets 用真实市值，加 today_pnl（portfolio_daily 最新）
2) 前端 Home.vue：totalAssets 用后端 total_assets；todayPnl 优先用后端 today_pnl
"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"

def read(p):
    with io.open(p, 'r', encoding='utf-8') as f:
        return f.read()

def write(p, s):
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)
    print('written:', p)

# ---------- 1. 后端 server.js ----------
p = os.path.join(BASE, 'server.js')
s = read(p)

old = """    const holdings = {};
    for (const [code, h] of Object.entries(portfolio.holdings || {})) {
      const fund = await new Promise((resolve) => {
        db.get('SELECT fund_name, fund_type FROM funds WHERE fund_code = ?', [code], (err, row) => resolve(err ? null : row));
      });
      const lastBuy = await new Promise((resolve) => {
        db.get("SELECT MAX(transaction_date) AS md FROM transactions WHERE user_id = ? AND fund_code = ? AND transaction_type = 'BUY'", [userId, code], (err, row) => resolve(err ? null : row));
      });
      const pending = !!(lastBuy && lastBuy.md && lastBuy.md.slice(0, 10) === todayStr);
      holdings[code] = { ...h, fund_name: fund ? fund.fund_name : code, fund_type: fund ? fund.fund_type : '', pending_confirm: pending };
    }
    res.json({
      initial_capital: portfolio.initial_capital,
      current_capital: portfolio.current_capital,
      holdings,
      total_assets: portfolio.current_capital + Object.values(portfolio.holdings).reduce((sum, h) => sum + h.total_cost, 0)
    });"""

new = """    const holdings = {};
    for (const [code, h] of Object.entries(portfolio.holdings || {})) {
      const fund = await new Promise((resolve) => {
        db.get('SELECT fund_name, fund_type FROM funds WHERE fund_code = ?', [code], (err, row) => resolve(err ? null : row));
      });
      const lastBuy = await new Promise((resolve) => {
        db.get("SELECT MAX(transaction_date) AS md FROM transactions WHERE user_id = ? AND fund_code = ? AND transaction_type = 'BUY'", [userId, code], (err, row) => resolve(err ? null : row));
      });
      const pending = !!(lastBuy && lastBuy.md && lastBuy.md.slice(0, 10) === todayStr);
      // 最新真实净值 + 市值（总资产/累计收益按市值口径，不能用成本）
      const navRow = await new Promise((resolve) => {
        db.get('SELECT unit_nav, nav_date, daily_return FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1', [code], (err, row) => resolve(err ? null : row));
      });
      const latestNav = navRow ? navRow.unit_nav : null;
      const marketValue = latestNav ? h.shares * latestNav : h.total_cost;
      holdings[code] = {
        ...h, fund_name: fund ? fund.fund_name : code, fund_type: fund ? fund.fund_type : '', pending_confirm: pending,
        latest_nav: latestNav, nav_date: navRow ? navRow.nav_date : null, daily_return: navRow ? navRow.daily_return : null,
        market_value: marketValue
      };
    }
    // 今日盈亏：取 portfolio_daily 最新快照（收盘按真实净值计算）
    const todayPnlRow = await new Promise((resolve) => {
      db.get('SELECT daily_pnl FROM portfolio_daily WHERE user_id = ? ORDER BY date DESC LIMIT 1', [userId], (err, row) => resolve(err ? null : row));
    });
    const marketValueTotal = Object.values(holdings).reduce((sum, h) => sum + (h.market_value || h.total_cost), 0);
    res.json({
      initial_capital: portfolio.initial_capital,
      current_capital: portfolio.current_capital,
      holdings,
      total_assets: portfolio.current_capital + marketValueTotal,
      today_pnl: todayPnlRow ? todayPnlRow.daily_pnl : 0
    });"""
assert s.count(old) == 1, 'ai/portfolio block not found'
s = s.replace(old, new)
write(p, s)

# ---------- 2. 前端 Home.vue ----------
p = os.path.join(BASE, 'frontend', 'src', 'views', 'Home.vue')
s = read(p)

# 2.1 totalAssets 用后端市值口径
old_ta = """const totalAssets = computed(() => {
  if (!portfolio.value) return 0
  const holdings = portfolio.value.holdings
  if (!holdings || typeof holdings !== 'object') return portfolio.value.current_capital || 0
  const holdingsValue = Object.values(holdings).reduce((sum: number, h: any) => sum + (h?.total_cost || 0), 0)
  return (portfolio.value.current_capital || 0) + holdingsValue
})"""
new_ta = """const totalAssets = computed(() => {
  // 后端已按真实市值计算 total_assets（现金 + 持仓市值），优先使用；兼容旧数据回退
  if (portfolio.value?.total_assets != null) return portfolio.value.total_assets
  if (!portfolio.value) return 0
  const holdings = portfolio.value.holdings
  if (!holdings || typeof holdings !== 'object') return portfolio.value.current_capital || 0
  const holdingsValue = Object.values(holdings).reduce((sum: number, h: any) => sum + (h?.market_value || h?.total_cost || 0), 0)
  return (portfolio.value.current_capital || 0) + holdingsValue
})"""
assert s.count(old_ta) == 1, 'totalAssets block not found'
s = s.replace(old_ta, new_ta)

# 2.2 todayPnl 优先用后端 today_pnl（真实快照），回退持仓聚合
old_tp = """const todayPnl = computed(() => {
  // 使用真实的今日盈亏数据
  return holdings.value.reduce((sum, h) => {
    if (h.today_pnl !== null && h.today_pnl !== undefined) {
      return sum + h.today_pnl
    }
    return sum
  }, 0)
})"""
new_tp = """const todayPnl = computed(() => {
  // 优先用后端 portfolio_daily 最新快照的当日盈亏（收盘按真实净值计算，覆盖盘中无当日净值场景）
  if (portfolio.value?.today_pnl != null) return portfolio.value.today_pnl
  // 回退：聚合持仓今日盈亏
  return holdings.value.reduce((sum, h) => {
    if (h.today_pnl !== null && h.today_pnl !== undefined) {
      return sum + h.today_pnl
    }
    return sum
  }, 0)
})"""
assert s.count(old_tp) == 1, 'todayPnl block not found'
s = s.replace(old_tp, new_tp)
write(p, s)

print('DONE')
