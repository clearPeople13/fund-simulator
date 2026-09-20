# -*- coding: utf-8 -*-
"""修复“今日盈亏待更新却显示-86.86”：快照只在当日净值公布后写入；净值同步后自动补当日快照；today_pnl 仅取当日确认值"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) saveDailySnapshot 加守卫：当日净值未公布不写快照
old1 = """// 保存某用户当日账户快照（真实数据，写入 portfolio_daily）
async function saveDailySnapshot(userId) {
  const portfolio = await getUserPortfolio(userId);"""
new1 = """// 保存某用户当日账户快照（真实数据，写入 portfolio_daily）
// 守卫：仅当“当日净值已公布”（fund_nav 最新净值日==今天）才写快照；
// 否则（盘中/净值未公布/非交易日）不写，避免用 T-1 净值产生伪确认盈亏。
async function saveDailySnapshot(userId) {
  const date = getLocalDateStr();
  const navLatest = await new Promise((resolve, reject) => {
    db.get('SELECT MAX(nav_date) AS d FROM fund_nav', [], (err, row) => err ? reject(err) : resolve(row ? row.d : null));
  });
  if (navLatest !== date) {
    return null;
  }
  const portfolio = await getUserPortfolio(userId);"""
assert s.count(old1) == 1, 'block1 not found'
s = s.replace(old1, new1)

# 2) 函数中部重复的 date 声明移除
old2 = """  const cash = portfolio.current_capital;
  const total = cash + marketValue;
  const date = getLocalDateStr();
"""
new2 = """  const cash = portfolio.current_capital;
  const total = cash + marketValue;
"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

# 3) 净值同步完成后，为所有用户生成当日确认快照
old3 = """    fetcher.close();
    console.log('[净值同步] 完成，新入库 ' + inserted + ' 条（区间 ' + startDate + ' 起）');"""
new3 = """    fetcher.close();
    console.log('[净值同步] 完成，新入库 ' + inserted + ' 条（区间 ' + startDate + ' 起）');
    // 净值公布后生成当日确认快照（真实净值口径，供资产走势/每日盈亏图使用）
    for (const userId of Object.keys(userConfigs)) {
      try {
        const snapshot = await saveDailySnapshot(userId);
        if (snapshot) console.log(`[净值同步] ${userConfigs[userId].name} 当日快照已确认: ${snapshot.date} 总资产¥${snapshot.total.toFixed(2)} 当日盈亏¥${snapshot.dailyPnl.toFixed(2)}`);
      } catch (snapErr) {
        console.error(`[净值同步] 保存快照失败 ${userId}: ${snapErr.message}`);
      }
    }"""
assert s.count(old3) == 1, 'block3 not found'
s = s.replace(old3, new3)

# 4) today_pnl 仅取“今日已确认”快照，无则 null（前端显示待更新）
old4 = """    // 今日盈亏：取 portfolio_daily 最新快照（收盘按真实净值计算）
    const todayPnlRow = await new Promise((resolve) => {
      db.get('SELECT daily_pnl FROM portfolio_daily WHERE user_id = ? ORDER BY date DESC LIMIT 1', [userId], (err, row) => resolve(err ? null : row));
    });"""
new4 = """    // 今日盈亏：仅取“今日已确认”快照（当日净值未公布时为 null，前端显示待更新）
    const todayPnlRow = await new Promise((resolve) => {
      db.get('SELECT daily_pnl FROM portfolio_daily WHERE user_id = ? AND date = ?', [userId, getLocalDateStr()], (err, row) => resolve(err ? null : row));
    });"""
assert s.count(old4) == 1, 'block4 not found'
s = s.replace(old4, new4)

old5 = """      today_pnl: todayPnlRow ? todayPnlRow.daily_pnl : 0,"""
new5 = """      today_pnl: todayPnlRow ? todayPnlRow.daily_pnl : null,"""
assert s.count(old5) == 1, 'block5 not found'
s = s.replace(old5, new5)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('server.js patched')
