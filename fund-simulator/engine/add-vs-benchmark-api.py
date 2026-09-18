# -*- coding: utf-8 -*-
"""server.js 新增 GET /api/ai/performance-vs-benchmark（账户累计收益率 vs 沪深300 累计涨幅）"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """// ===== 单基金费率（申购/赎回阶梯/管理/托管，真实 fund_fees）====="""
new = """// 账户累计收益率 vs 沪深300 基准（AI 操盘相对指数表现）
app.get('/api/ai/performance-vs-benchmark', async (req, res) => {
  const qall = (sql, params = []) => new Promise((resolve, reject) => db.all(sql, params, (e, r) => e ? reject(e) : resolve(r || [])));
  try {
    const userId = req.query.user_id || currentUser;
    const snaps = await qall('SELECT date, total_assets FROM portfolio_daily WHERE user_id = ? ORDER BY date ASC', [userId]);
    const cfg = await new Promise((resolve) => db.get('SELECT initial_capital FROM user_configs WHERE user_id = ?', [userId], (e, r) => resolve(r || null)));
    const initial = (cfg && cfg.initial_capital) || 100000;
    const bench = await qall('SELECT date, value FROM benchmark_daily ORDER BY date ASC');
    const accMap = {}, benchMap = {};
    snaps.forEach(s => { accMap[s.date] = Math.round((s.total_assets / initial - 1) * 10000) / 100; });
    if (bench.length) {
      const base = bench[0].value || 1;
      bench.forEach(b => { benchMap[b.date] = Math.round((b.value / base - 1) * 10000) / 100; });
    }
    const dates = [...new Set([...Object.keys(accMap), ...Object.keys(benchMap)])].sort();
    res.json({
      initial_capital: initial,
      series: dates.map(d => ({
        date: d,
        account_pct: accMap[d] != null ? accMap[d] : null,
        bench_pct: benchMap[d] != null ? benchMap[d] : null
      }))
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ===== 单基金费率（申购/赎回阶梯/管理/托管，真实 fund_fees）====="""
assert s.count(old) == 1, 'anchor not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('performance-vs-benchmark api added')
