import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 逐个删除已抽到 routes/readonly.js 的路由块（按唯一字符串精确匹配）
blocks = [
  # /api/performance/:user_id
  """app.get('/api/performance/:user_id', async (req, res) => {
  try {
    const rows = await new Promise((resolve, reject) => {
      db.all('SELECT * FROM performance_daily WHERE user_id = ? ORDER BY date', [req.params.user_id], (err, rows) => err ? reject(err) : resolve(rows || []));
    });
    res.json({ user_id: req.params.user_id, performance: rows });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

""",
  # /api/benchmark
  """app.get('/api/benchmark', async (req, res) => {
  try {
    const limit = Math.min(parseInt(req.query.limit) || 60, 500);
    const rows = await new Promise((resolve, reject) => {
      db.all('SELECT * FROM benchmark_daily ORDER BY date DESC LIMIT ?', [limit], (err, rows) => err ? reject(err) : resolve(rows || []));
    });
    res.json({ benchmark: rows.reverse() });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

""",
  # /api/reports
  """app.get('/api/reports', async (req, res) => {
  try {
    const userId = req.query.user_id || currentUser;
    const type = req.query.type || 'weekly';
    const rows = await new Promise((resolve, reject) => {
      db.all('SELECT * FROM reports WHERE user_id = ? AND report_type = ? ORDER BY id DESC LIMIT 10', [userId, type], (err, rows) => err ? reject(err) : resolve(rows || []));
    });
    res.json({ user_id: userId, reports: rows });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

""",
  # /api/funds/:code/profile
  """app.get('/api/funds/:code/profile', (req, res) => {
  db.get('SELECT * FROM fund_profiles WHERE fund_code = ?', [req.params.code], (err, row) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ profile: row || null });
  });
});

""",
  # /api/funds/:code/research
  """app.get('/api/funds/:code/research', (req, res) => {
  const userId = req.query.user_id || currentUser;
  const limit = Math.min(parseInt(req.query.limit) || 20, 100);
  db.all('SELECT * FROM research_notes WHERE user_id = ? AND fund_code = ? ORDER BY id DESC LIMIT ?', [userId, req.params.code, limit], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ notes: rows || [] });
  });
});

""",
  # /api/alerts
  """app.get('/api/alerts', (req, res) => {
  const userId = req.query.user_id || currentUser;
  const limit = Math.min(parseInt(req.query.limit) || 50, 200);
  db.all('SELECT * FROM risk_events WHERE user_id = ? ORDER BY id DESC LIMIT ?', [userId, limit], (err, events) => {
    if (err) return res.status(500).json({ error: err.message });
    db.all('SELECT * FROM data_quality_logs ORDER BY id DESC LIMIT 20', [], (err2, dq) => {
      if (err2) return res.status(500).json({ error: err2.message });
      res.json({ events: events || [], data_quality: dq || [] });
    });
  });
});

""",
  # /api/market-env
  """app.get('/api/market-env', (req, res) => {
  db.all('SELECT * FROM market_env ORDER BY date DESC LIMIT 30', [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ market: rows || [] });
  });
});

""",
  # /api/daily-recap
  """app.get('/api/daily-recap', (req, res) => {
  const userId = req.query.user_id || currentUser;
  db.all('SELECT * FROM reports WHERE user_id = ? AND report_type = ? ORDER BY id DESC LIMIT 7', [userId, 'daily'], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ recaps: rows || [] });
  });
});

""",
  # /api/reports/:id
  """app.get('/api/reports/:id', (req, res) => {
  db.get('SELECT * FROM reports WHERE id = ?', [req.params.id], (err, row) => {
    if (err) return res.status(500).json({ error: err.message });
    if (!row) return res.status(404).json({ error: '报告不存在' });
    res.json({ report: row });
  });
});

""",
  # /api/risk/events
  """app.get('/api/risk/events', (req, res) => {
  const userId = req.query.user_id || currentUser;
  const limit = Math.min(parseInt(req.query.limit) || 50, 200);
  db.all('SELECT * FROM risk_events WHERE user_id = ? ORDER BY id DESC LIMIT ?', [userId, limit], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ events: rows });
  });
});

""",
  # /api/risk/params/:user_id
  """app.get('/api/risk/params/:user_id', async (req, res) => {
  try {
    const cfg = await getRiskParams(req.params.user_id);
    res.json({ user_id: req.params.user_id, params: cfg });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

""",
  # /api/orders
  """app.get('/api/orders', (req, res) => {
  const userId = req.query.user_id || currentUser;
  const limit = Math.min(parseInt(req.query.limit) || 50, 200);
  db.all('SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT ?', [userId, limit], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ orders: rows });
  });
});

""",
]
for i, b in enumerate(blocks):
  cnt = s.count(b)
  if cnt != 1:
    print(f'WARN block {i} count={cnt}')
  s = s.replace(b, '')

# /api/audit 块（跨多行，单独处理）
audit_start = "app.get('/api/audit', (req, res) => {"
ai = s.find(audit_start)
if ai != -1:
  # 找到这个路由块结束（下一个 app. 或 // 注释）
  nxt = s.find("\napp.", ai + 10)
  if nxt != -1:
    s = s[:ai] + "// /api/audit 已抽到 routes/readonly.js\n" + s[nxt:]

# 挂载 readonly 路由
old_mount = "// 挂载用户路由（必须在 SPA fallback 之前）"
new_mount = """// 挂载只读查询路由（必须在 SPA fallback 之前）
app.use('/api', require('./routes/readonly')({ db, getCurrentUser, getRiskParams }));

// 挂载用户路由（必须在 SPA fallback 之前）"""
assert s.count(old_mount) == 1
s = s.replace(old_mount, new_mount)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('readonly routes extracted, size now:', len(s))
