import io

# 1) readonly.js 加 /ai/daily
p1 = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\routes\readonly.js"
with io.open(p1, 'r', encoding='utf-8') as f:
    s1 = f.read()
old = "  r.get('/daily-recap', (req, res) => {"
new = """  r.get('/ai/daily', async (req, res) => {
    try {
      const userId = req.query.user_id || getCurrentUser();
      const rows = await new Promise((resolve, reject) => {
        db.all('SELECT date, total_assets, daily_pnl, cash, market_value FROM portfolio_daily WHERE user_id = ? ORDER BY date ASC', [userId], (e, rows) => e ? reject(e) : resolve(rows || []));
      });
      res.json(rows);
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.get('/daily-recap', (req, res) => {"""
assert s1.count(old) == 1
s1 = s1.replace(old, new)
with io.open(p1, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s1)

# 2) server.js 删 /api/ai/daily 块
p2 = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p2, 'r', encoding='utf-8') as f:
    s2 = f.read()
old2 = """// 获取每日账户快照（资产走势/每日盈亏图真实数据）
app.get('/api/ai/daily', async (req, res) => {
  try {
    const userId = req.query.user_id || currentUser;
    const rows = await new Promise((resolve, reject) => {
      db.all('SELECT date, total_assets, daily_pnl, cash, market_value FROM portfolio_daily WHERE user_id = ? ORDER BY date ASC', [userId], (err, rows) => {
        if (err) reject(err); else resolve(rows || []);
      });
    });
    res.json(rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

"""
assert s2.count(old2) == 1
s2 = s2.replace(old2, '// /api/ai/daily 已抽到 routes/readonly.js\n')
with io.open(p2, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s2)
print('ai/daily moved')
