# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js'
c = io.open(p, encoding='utf-8').read()

# 1. KEEP=8 硬上限 → 不设固定上限（防御性 MAX_POOL=25，手动项不限量）
old = """  candidates.sort((a, b) => b.score - a.score);
  const KEEP = 8;

  // 同策略 A/C/D 份额去重：同一基金只留评分最高的一只（避免观察池被重复份额占位）
  const seenKey = new Set();
  const deduped = [];
  for (const cd of candidates) {
    const key = (cd.fund_name || '').replace(/[ACDE]$/, '');
    if (seenKey.has(key)) continue;
    seenKey.add(key);
    deduped.push(cd);
  }

  const picked = deduped.slice(0, KEEP);

  const inserted = [];
  // AI 池全量重建：先清空本用户全部 AI 项，再写入最新排名（强制收敛到 KEEP 只）
  const removedCount = await new Promise((resolve, reject) => {
    db.run("DELETE FROM watchlist WHERE user_id = ? AND source = 'ai'", [userId], function (err) {
      if (err) reject(err); else resolve(this.changes || 0);
    });
  });
  // 候选顺位队列：净值不足 30 条的新基金跳过并自动补位（宁缺毋滥，但尽量凑满 KEEP）
  const pickedQueue = deduped.slice(0, Math.max(KEEP, Math.min(deduped.length, KEEP * 3)));
  for (const fund of pickedQueue) {
    // 新基金：入库 funds + 拉全量历史净值；净值不足 30 条的不入池（无法出信号）
    if (inserted.length >= KEEP) break;"""
new = """  candidates.sort((a, b) => b.score - a.score);
  // 观察池不设固定上限：AI 按全市场扫描排名动态维持（排名靠前即入池、掉队自动淘汰）。
  // MAX_POOL 仅为防御性上限（防止净值拉取与页面压力），手动添加的自选不限量。
  const MAX_POOL = 25;

  // 同策略 A/C/D 份额去重：同一基金只留评分最高的一只（避免观察池被重复份额占位）
  const seenKey = new Set();
  const deduped = [];
  for (const cd of candidates) {
    const key = (cd.fund_name || '').replace(/[ACDE]$/, '');
    if (seenKey.has(key)) continue;
    seenKey.add(key);
    deduped.push(cd);
  }

  const inserted = [];
  // AI 池全量重建：先清空本用户全部 AI 项，再写入最新扫描排名（观察池随市场动态流动）
  const removedCount = await new Promise((resolve, reject) => {
    db.run("DELETE FROM watchlist WHERE user_id = ? AND source = 'ai'", [userId], function (err) {
      if (err) reject(err); else resolve(this.changes || 0);
    });
  });
  // 候选顺位队列：净值不足 30 条的新基金跳过并自动补位（宁缺毋滥，尽量凑满观察池）
  const pickedQueue = deduped.slice(0, Math.max(MAX_POOL, Math.min(deduped.length, MAX_POOL * 3)));
  for (const fund of pickedQueue) {
    // 新基金：入库 funds + 拉全量历史净值；净值不足 30 条的不入池（无法出信号）
    if (inserted.length >= MAX_POOL) break;"""
assert c.count(old) == 1, 'KEEP %d' % c.count(old)
c = c.replace(old, new, 1)

# 2. 观察池周期扫描调度：每日 09:35（盘前，用昨收净值快照）+ 17:00（盘后，当日净值基本更新完）
anchor = "// 全市场基金库每日刷新（rankhandler 快照，供 AI 全市场选基与基金库展示；子进程不阻塞主服务）"
scan_schedule = """// 观察池周期扫描：AI 每日 09:35（盘前）+ 17:00（盘后）自动重扫全市场并更新观察池（真实扫描、持续动起来；后台执行不阻塞）
function scheduleWatchlistScan() {
  const runOnce = () => {
    autoDiscoverOnStartup().then(() => console.log('[观察池扫描] 本轮回合完成'));
  };
  const scheduleAt = (hour, minute) => {
    const now = new Date();
    const target = new Date(now);
    target.setHours(hour, minute, 0, 0);
    if (now > target) target.setDate(target.getDate() + 1);
    const delay = target.getTime() - now.getTime();
    setTimeout(() => {
      runOnce();
      setInterval(runOnce, 24 * 60 * 60 * 1000);
    }, delay);
    return target;
  };
  const t1 = scheduleAt(9, 35);
  const t2 = scheduleAt(17, 0);
  console.log('[观察池扫描] 每日 09:35 盘前 + 17:00 盘后自动重扫全市场（首次 ' + t1.toLocaleString() + ' / ' + t2.toLocaleString() + '）');
}

"""
assert c.count(anchor) == 1, 'anchor %d' % c.count(anchor)
c = c.replace(anchor, scan_schedule + anchor, 1)

# 3. 启动调用
old2 = """  scheduleAnalysis();
  scheduleUniverseSync();"""
new2 = """  scheduleAnalysis();
  scheduleUniverseSync();
  scheduleWatchlistScan();"""
assert c.count(old2) == 1, 'boot %d' % c.count(old2)
c = c.replace(old2, new2, 1)

io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
