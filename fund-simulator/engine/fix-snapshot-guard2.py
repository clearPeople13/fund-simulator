# -*- coding: utf-8 -*-
"""守卫改为“持仓基金当日净值全部公布”才写快照；净值同步增加 22:30 补充（净值陆续公布）"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) 守卫修正：按该用户持仓基金逐一检查当日净值是否公布
old1 = """async function saveDailySnapshot(userId) {
  const date = getLocalDateStr();
  const navLatest = await new Promise((resolve, reject) => {
    db.get('SELECT MAX(nav_date) AS d FROM fund_nav', [], (err, row) => err ? reject(err) : resolve(row ? row.d : null));
  });
  if (navLatest !== date) {
    return null;
  }
  const portfolio = await getUserPortfolio(userId);"""
new1 = """async function saveDailySnapshot(userId) {
  const date = getLocalDateStr();
  // 守卫：仅当该用户全部持仓基金的当日净值均已公布才写快照；
  // 任一持仓基金当日净值未公布（陆续公布中）→ 不写，避免用 T-1 净值产生伪确认盈亏。
  const holdingCodes = await new Promise((resolve, reject) => {
    db.all('SELECT DISTINCT fund_code FROM holdings WHERE user_id = ?', [userId], (err, rows) => err ? reject(err) : resolve((rows || []).map(r => r.fund_code)));
  });
  if (holdingCodes.length === 0) return null; // 无持仓不写（今日盈亏由前端按空持仓处理为 0）
  for (const code of holdingCodes) {
    const nav = await new Promise((resolve, reject) => {
      db.get('SELECT nav_date FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1', [code], (err, row) => err ? reject(err) : resolve(row));
    });
    if (!nav || nav.nav_date !== date) return null;
  }
  const portfolio = await getUserPortfolio(userId);"""
assert s.count(old1) == 1, 'block1 not found'
s = s.replace(old1, new1)

# 2) scheduleNavSync 增加 22:30 补充同步
old2 = """  console.log('[净值同步] 每日 21:30 自动拉取当日净值（首次 ' + target.toLocaleString() + '）');
  // 启动时立即补一次（防止停机期间数据缺失）
  setTimeout(run, 15 * 1000);
}"""
new2 = """  console.log('[净值同步] 每日 21:30 自动拉取当日净值（首次 ' + target.toLocaleString() + '）');
  // 22:30 补充同步：基金净值陆续公布（部分 22-23 点才出），确保当日确认快照完整
  const target2 = new Date(now);
  target2.setHours(22, 30, 0, 0);
  if (now > target2) target2.setDate(target2.getDate() + 1);
  const delay2 = target2.getTime() - now.getTime();
  setTimeout(() => {
    run();
    setInterval(run, 24 * 60 * 60 * 1000);
  }, delay2);
  console.log('[净值同步] 每日 22:30 补充同步（首次 ' + target2.toLocaleString() + '）');
  // 启动时立即补一次（防止停机期间数据缺失）
  setTimeout(run, 15 * 1000);
}"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('server.js patched')
