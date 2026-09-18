# -*- coding: utf-8 -*-
"""修复 saveDailySnapshot 守卫：当日买入（T+1 待确认，市值=成本）的持仓不要求当日净值，
否则如 000001 当日买入未公布净值会阻塞整日快照写入"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """  if (holdingCodes.length === 0) return null; // 无持仓不写（今日盈亏由前端按空持仓处理为 0）
  for (const code of holdingCodes) {
    const nav = await new Promise((resolve, reject) => {
      db.get('SELECT nav_date FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1', [code], (err, row) => err ? reject(err) : resolve(row));
    });
    if (!nav || nav.nav_date !== date) return null;
  }"""
new = """  if (holdingCodes.length === 0) return null; // 无持仓不写（今日盈亏由前端按空持仓处理为 0）
  for (const code of holdingCodes) {
    // T+1：当日买入的持仓当日按成本计市值（无收益），不依赖当日净值 → 跳过净值检查
    const lastBuy = await new Promise((resolve, reject) => {
      db.get("SELECT transaction_date FROM transactions WHERE user_id = ? AND fund_code = ? AND transaction_type = 'BUY' ORDER BY transaction_date DESC LIMIT 1",
        [userId, code], (err, row) => err ? reject(err) : resolve(row));
    });
    const pendingBuy = !!lastBuy && isSameLocalDay(lastBuy.transaction_date);
    if (pendingBuy) continue;
    const nav = await new Promise((resolve, reject) => {
      db.get('SELECT nav_date FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1', [code], (err, row) => err ? reject(err) : resolve(row));
    });
    if (!nav || nav.nav_date !== date) return null;
  }"""
assert s.count(old) == 1, 'block not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('server.js guard fixed')
