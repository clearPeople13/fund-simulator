# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js'
c = io.open(p, encoding='utf-8').read()

# ========== 1. 替换 aiDiscoverWatchlist 整个函数 ==========
old_fn_start = "// AI 按用户性格自主选基并维护观察池（source='ai'，上限 8 只；手动项永不删除；只影响观察池，不涉及交易）"
old_fn_end = "// 本地时区日期字符串（YYYY-MM-DD）"
i0 = c.index(old_fn_start)
i1 = c.index(old_fn_end)
old_fn = c[i0:i1]

new_fn = """// AI 按用户性格从全市场自主选基并维护观察池（source='ai'，上限 KEEP 只；手动项永不删除；只影响观察池，不涉及交易）
// 候选池 = 全市场基金库 fund_universe（天天基金排行快照，股票型/混合型/指数型/QDII 共 1.4万+ 只）
async function aiDiscoverWatchlist(userId) {
  const user = userConfigs[userId];
  if (!user) throw new Error('用户不存在');
  const style = user.style || '稳健型';
  const risk = user.risk_tolerance || 'medium';

  // 现有观察池：区分手动（保留）与 AI（由 AI 重排维护）
  const existing = await getWatchlist(userId);
  const manualSet = new Set(existing.filter(x => x.source !== 'ai').map(x => x.fund_code));
  const aiSet = new Set(existing.filter(x => x.source === 'ai').map(x => x.fund_code));

  // 跨用户去重：其他用户的观察池（全部来源）与持仓，本用户 AI 不再重复关注（性格分工）
  const otherWatchSet = await new Promise((resolve) => {
    db.all('SELECT DISTINCT fund_code FROM watchlist WHERE user_id != ?', [userId], (err, rows) => {
      resolve(err ? new Set() : new Set((rows || []).map(r => r.fund_code)));
    });
  });
  const otherHoldSet = await new Promise((resolve) => {
    db.all('SELECT DISTINCT fund_code FROM holdings WHERE user_id != ? AND shares > 0', [userId], (err, rows) => {
      resolve(err ? new Set() : new Set((rows || []).map(r => r.fund_code)));
    });
  });

  // 全市场候选：fund_universe（含多周期涨幅快照）
  const universe = await new Promise((resolve) => {
    db.all('SELECT fund_code, fund_name, fund_type, unit_nav, day_return, r1m, r3m, r6m, r1y, inception_date, scale FROM fund_universe',
      (err, rows) => resolve(err ? [] : (rows || [])));
  });
  console.log(`[全市场选基] ${userId}（${style}）全市场候选 ${universe.length} 只`);

  const THEME_RE = /新能源|白酒|能源|成长|消费|科技|军工|医药|互联网|半导体|芯片|数字|人工智能|创新|制造|改革|新兴/;
  const MIN_SCALE = 2;             // 剔除迷你基金（规模 < 2 亿元）
  const CUTOFF_DATE = '2025-09-18'; // 成立满 1 年才参与（有完整周期可评分）

  const candidates = [];
  for (const f of universe) {
    if (!f.unit_nav || f.unit_nav <= 0) continue;
    if (f.scale != null && f.scale < MIN_SCALE) continue;
    if (f.inception_date && f.inception_date > CUTOFF_DATE) continue;
    if (manualSet.has(f.fund_code)) continue;
    if (otherWatchSet.has(f.fund_code)) continue;
    if (otherHoldSet.has(f.fund_code)) continue;

    const theme = THEME_RE.test(f.fund_name || '');
    const r1y = f.r1y != null ? f.r1y : 0;
    const r3m = f.r3m != null ? f.r3m : 0;
    const r6m = f.r6m != null ? f.r6m : 0;
    const day = f.day_return != null ? f.day_return : 0;

    let matched = false;
    let score = 0;
    if (risk === 'high') {
      // 激进：高弹性类型（股票型/QDII）∪ 任何行业主题基金；弹性 = 强动量 + 主题溢价 + 超跌反弹空间
      if (f.fund_type === '股票型' || f.fund_type === 'QDII' || theme) matched = true;
      if (matched) {
        score = Math.max(r1y, 0) * 0.5 + Math.max(r3m, 0) * 0.6 + Math.max(day, 0) * 1.2
          + (theme ? 3 : 0) + (f.fund_type === '股票型' ? 2 : 0)
          + (r6m < 0 ? Math.min(Math.abs(r6m) * 0.15, 5) : 0);
      }
    } else {
      // 稳健：非主题的宽基/均衡（指数型/混合型）；稳定 = 长期正收益 + 回撤控制 + 温和动量
      if ((f.fund_type === '指数型' || f.fund_type === '混合型') && !theme) matched = true;
      if (matched) {
        score = Math.max(r1y, 0) * 0.8 + Math.max(r6m, 0) * 0.4 + Math.max(day, 0) * 0.5
          + (r3m >= 0 ? 1.5 : 0) + (r6m < -15 ? -4 : 0) + (f.fund_type === '指数型' ? 2 : 0);
      }
    }
    if (!matched) continue;
    candidates.push({ fund_code: f.fund_code, fund_name: f.fund_name, fund_type: f.fund_type, score: Number(score.toFixed(2)), unit_nav: f.unit_nav, r1y, r6m, day });
  }

  candidates.sort((a, b) => b.score - a.score);
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
      db.run('INSERT OR IGNORE INTO watchlist (user_id, fund_code, reason, source) VALUES (?, ?, ?, \'ai\')',
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
  return { inserted, removed, kept: picked.length, total: candidates.length, universe: universe.length };
}

// 新基金入库 funds 并拉全量历史净值（观察池/信号/交易都依赖 fund_nav）
async function ensureFundWithNav(f) {
  const inFunds = await new Promise((resolve) => {
    db.get('SELECT fund_code FROM funds WHERE fund_code = ?', [f.fund_code], (err, row) => resolve(err ? null : row));
  });
  if (inFunds) return;
  // 粗类 → 细类映射（universe 只有 股票型/混合型/指数型/QDII 四大类）
  let ft = '混合型-偏股';
  if (f.fund_type === '股票型') ft = '股票型';
  else if (f.fund_type === '指数型') ft = '指数型-股票';
  else if (f.fund_type === 'QDII') ft = 'QDII-普通股票';
  else if (/新能源|白酒|能源|科技|军工|医药|半导体|芯片|数字|人工智能|互联网/.test(f.fund_name || '')) ft = '混合型-偏股';
  else ft = '混合型-灵活';
  await new Promise((resolve, reject) => {
    db.run('INSERT INTO funds (fund_code, fund_name, fund_type) VALUES (?, ?, ?)', [f.fund_code, f.fund_name, ft], (err) => err ? reject(err) : resolve());
  });
  try {
    const fetcher = new FundDataFetcher();
    const navList = await fetcher.getNavHistoryAll(f.fund_code, '', '', 400);
    if (navList.length) await fetcher.saveNavData(navList);
    fetcher.close();
    console.log(`[全市场选基] 新基金入库+历史净值: ${f.fund_code} ${f.fund_name}（${ft}）共 ${navList.length} 条`);
  } catch (e) {
    console.error(`[全市场选基] ${f.fund_code} 净值拉取失败: ${e.message}`);
  }
}

"""
c = c[:i0] + new_fn + c[i1:]

io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK aiDiscoverWatchlist 全市场版')
