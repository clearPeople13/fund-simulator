# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js'
c = io.open(p, encoding='utf-8').read()

# ========== 1. 稳健评分：指数型主导（+6 分），降低主动混合近1年权重的绝对优势 ==========
old = """        score = Math.max(r1y, 0) * 0.8 + Math.max(r6m, 0) * 0.4 + Math.max(day, 0) * 0.5
          + (r3m >= 0 ? 1.5 : 0) + (r6m < -15 ? -4 : 0) + (f.fund_type === '指数型' ? 2 : 0);"""
new = """        score = Math.max(r1y, 0) * 0.5 + Math.max(r6m, 0) * 0.3 + Math.max(day, 0) * 0.3
          + (r3m >= 0 ? 1.0 : 0) + (r6m < -15 ? -4 : 0) + (f.fund_type === '指数型' ? 6 : 0);"""
assert c.count(old) == 1, 'score count %d' % c.count(old)
c = c.replace(old, new, 1)

# ========== 2. picked 补位：净值不足 30 条的被跳过时，从候选后续补足 KEEP ==========
old2 = """  const picked = deduped.slice(0, KEEP);

  const inserted = [];
  // AI 池全量重建：先清空本用户全部 AI 项，再写入最新排名（强制收敛到 KEEP 只）
  const removedCount = await new Promise((resolve, reject) => {
    db.run("DELETE FROM watchlist WHERE user_id = ? AND source = 'ai'", [userId], function (err) {
      if (err) reject(err); else resolve(this.changes || 0);
    });
  });
  for (const fund of picked) {
    // 新基金：入库 funds + 拉全量历史净值；净值不足 30 条的不入池（无法出信号）
    const navCount = await ensureFundWithNav(fund);
    if (navCount < 30) continue;"""
new2 = """  const picked = deduped.slice(0, KEEP);

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
    if (inserted.length >= KEEP) break;
    const navCount = await ensureFundWithNav(fund);
    if (navCount < 30) continue;"""
assert c.count(old2) == 1, 'pick count %d' % c.count(old2)
c = c.replace(old2, new2, 1)

io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
