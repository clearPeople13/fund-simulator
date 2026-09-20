# -*- coding: utf-8 -*-
"""server.js 新增 GET /api/market/overview（市场行情概览：指数走势 + 市场温度 + 全市场涨跌统计）"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """app.get('/api/ai/hotspots', async (req, res) => {"""
new = """// 市场行情概览：基准指数走势 + 市场温度 + 全市场基金涨跌统计
app.get('/api/market/overview', async (req, res) => {
  const qall = (sql, params = []) => new Promise((resolve, reject) => db.all(sql, params, (e, r) => e ? reject(e) : resolve(r || [])));
  try {
    const days = Math.min(parseInt(req.query.days || '90', 10) || 90, 365);
    const bench = await qall("SELECT date, value, change_pct FROM benchmark_daily ORDER BY date DESC LIMIT ?", [days]);
    bench.reverse();
    const env = await qall('SELECT * FROM market_env ORDER BY date DESC LIMIT 1');
    const stat = await qall("SELECT day_return FROM fund_universe WHERE day_return IS NOT NULL");
    let up = 0, down = 0, flat = 0, sum = 0;
    for (const r of stat) {
      if (r.day_return > 0.0001) up++;
      else if (r.day_return < -0.0001) down++;
      else flat++;
      sum += r.day_return;
    }
    const n = stat.length || 1;
    const bench5 = bench.slice(-5);
    res.json({
      benchmark: bench,
      market_env: env[0] || null,
      stats: {
        fund_count: stat.length,
        up, down, flat,
        avg_return: Math.round(sum / n * 100) / 100,
        up_pct: Math.round(up / n * 1000) / 10,
        bench_5d: bench5.map(b => ({ date: b.date, change_pct: Math.round(b.change_pct * 100) / 100 }))
      }
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/api/ai/hotspots', async (req, res) => {"""
assert s.count(old) == 1, 'anchor not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('market overview api added')
