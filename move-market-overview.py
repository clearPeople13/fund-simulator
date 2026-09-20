import io

# 1) readonly.js 加 /market/overview
p1 = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\routes\readonly.js"
with io.open(p1, 'r', encoding='utf-8') as f:
    s1 = f.read()
old = "  r.get('/ai/daily', async (req, res) => {"
new = """  r.get('/market/overview', async (req, res) => {
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
          fund_count: stat.length, up, down, flat,
          avg_return: Math.round(sum / n * 100) / 100,
          up_pct: Math.round(up / n * 1000) / 10,
          bench_5d: bench5.map(b => ({ date: b.date, change_pct: Math.round(b.change_pct * 100) / 100 }))
        }
      });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.get('/ai/daily', async (req, res) => {"""
assert s1.count(old) == 1
s1 = s1.replace(old, new)
with io.open(p1, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s1)

# 2) server.js 删 /api/market/overview 块
p2 = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p2, 'r', encoding='utf-8') as f:
    s2 = f.read()
old2 = """app.get('/api/market/overview', async (req, res) => {
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

"""
assert s2.count(old2) == 1
s2 = s2.replace(old2, '// /api/market/overview 已抽到 routes/readonly.js\n')
with io.open(p2, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s2)
print('market/overview moved')
