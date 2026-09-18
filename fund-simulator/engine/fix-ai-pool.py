# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js'
c = io.open(p, encoding='utf-8').read()

# ========== 1. THEME_RE 补主题词 ==========
old = "const THEME_RE = /新能源|白酒|能源|成长|消费|科技|军工|医药|互联网|半导体|芯片|集成电路|数字|人工智能|创新|制造|改革|新兴|软件|传媒|游戏|化工|有色|农业|电子|通信|计算机|机器人|高端装备/;"
new = "const THEME_RE = /新能源|白酒|能源|成长|消费|科技|军工|医药|互联网|半导体|芯片|集成电路|数字|人工智能|创新|制造|改革|新兴|软件|传媒|游戏|化工|有色|农业|电子|通信|计算机|机器人|高端装备|主题/;"
assert c.count(old) == 1, 'theme count %d' % c.count(old)
c = c.replace(old, new, 1)

# ========== 2. 重写入选/淘汰逻辑：先清空 AI 项再重建（强制收敛 KEEP）+ A/C 份额去重 + 净值门槛 ==========
old2 = """  candidates.sort((a, b) => b.score - a.score);
  const KEEP = 8;
  const picked = candidates.slice(0, KEEP);
  const pickedSet = new Set(picked.map(p => p.fund_code));

  const inserted = [];
  const removed = [];
  for (const fund of picked) {
    // 新基金：入库 funds + 拉全量历史净值（观察池基金必须能出信号）
    await ensureFundWithNav(fund);
    const reason = `AI按${style}自动筛选（全市场 ${candidates.length} 只候选）：近1年 ${fund.r1y >= 0 ? '+' : ''}${fund.r1y}%，近6月 ${fund.r6m >= 0 ? '+' : ''}${fund.r6m}%，日增长 ${fund.day >= 0 ? '+' : ''}${fund.day}%`;
    await new Promise((resolve, reject) => {
      db.run("INSERT OR IGNORE INTO watchlist (user_id, fund_code, reason, source) VALUES (?, ?, ?, 'ai')",
        [userId, fund.fund_code, reason],
        function (err) {
          if (err) reject(err);
          else {
            if (this.changes > 0) inserted.push(fund.fund_code);
            resolve();
          }
        });
    });
  }
  // 淘汰未进最新排名的旧 AI 项（AI 自主优胜劣汰）
  for (const code of aiSet) {
    if (!pickedSet.has(code)) {
      await new Promise((resolve, reject) => {
        db.run("DELETE FROM watchlist WHERE user_id = ? AND fund_code = ? AND source = 'ai'", [userId, code], (err) => {
          if (err) reject(err); else resolve();
        });
      });
      removed.push(code);
    }
  }
  return { inserted, removed, kept: picked.length, total: candidates.length, universe: universe.length };"""
new2 = """  candidates.sort((a, b) => b.score - a.score);
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
    db.run("DELETE FROM watchlist WHERE user_id = ? AND source = 'ai'", [userId], (err) => err ? reject(err) : resolve());
  });
  for (const fund of picked) {
    // 新基金：入库 funds + 拉全量历史净值；净值不足 30 条的不入池（无法出信号）
    const navCount = await ensureFundWithNav(fund);
    if (navCount < 30) continue;
    const reason = `AI按${style}自动筛选（全市场 ${candidates.length} 只候选）：近1年 ${fund.r1y >= 0 ? '+' : ''}${fund.r1y}%，近6月 ${fund.r6m >= 0 ? '+' : ''}${fund.r6m}%，日增长 ${fund.day >= 0 ? '+' : ''}${fund.day}%`;
    await new Promise((resolve, reject) => {
      db.run("INSERT OR IGNORE INTO watchlist (user_id, fund_code, reason, source) VALUES (?, ?, ?, 'ai')",
        [userId, fund.fund_code, reason],
        function (err) {
          if (err) reject(err);
          else {
            if (this.changes > 0) inserted.push(fund.fund_code);
            resolve();
          }
        });
    });
  }
  return { inserted, removed: removedCount, kept: inserted.length, total: candidates.length, universe: universe.length };"""
assert c.count(old2) == 1, 'fn body count %d' % c.count(old2)
c = c.replace(old2, new2, 1)

# ========== 3. ensureFundWithNav 返回净值条数；已在库的返回已有条数 ==========
old3 = """async function ensureFundWithNav(f) {
  const inFunds = await new Promise((resolve) => {
    db.get('SELECT fund_code FROM funds WHERE fund_code = ?', [f.fund_code], (err, row) => resolve(err ? null : row));
  });
  if (inFunds) return;"""
new3 = """async function ensureFundWithNav(f) {
  const inFunds = await new Promise((resolve) => {
    db.get('SELECT fund_code FROM funds WHERE fund_code = ?', [f.fund_code], (err, row) => resolve(err ? null : row));
  });
  if (inFunds) {
    const navN = await new Promise((resolve) => {
      db.get('SELECT COUNT(*) n FROM fund_nav WHERE fund_code = ?', [f.fund_code], (err, row) => resolve(err ? 0 : (row ? row.n : 0)));
    });
    return navN;
  }"""
assert c.count(old3) == 1, 'ensure count %d' % c.count(old3)
c = c.replace(old3, new3, 1)

# 返回值：拉净值后返回条数
old4 = """    fetcher.close();
    console.log(`[全市场选基] 新基金入库+历史净值: ${f.fund_code} ${f.fund_name}（${ft}）共 ${navList.length} 条`);
  } catch (e) {
    console.error(`[全市场选基] ${f.fund_code} 净值拉取失败: ${e.message}`);
  }
}"""
new4 = """    fetcher.close();
    console.log(`[全市场选基] 新基金入库+历史净值: ${f.fund_code} ${f.fund_name}（${ft}）共 ${navList.length} 条`);
    return navList.length;
  } catch (e) {
    console.error(`[全市场选基] ${f.fund_code} 净值拉取失败: ${e.message}`);
    return 0;
  }
}"""
assert c.count(old4) == 1, 'ensure tail count %d' % c.count(old4)
c = c.replace(old4, new4, 1)

io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
