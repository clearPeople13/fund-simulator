import io

# 1) server.js 删旧 transactions 块
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()
old = """// 获取AI交易记录
app.get('/api/ai/transactions', async (req, res) => {
  try {
    const userId = req.query.user_id || currentUser;
    const portfolio = await getUserPortfolio(userId);
    const txs = portfolio.transactions || [];
    // 附带真实基金名称（JOIN funds，取代前端硬编码映射）
    const enriched = [];
    for (const tx of txs) {
      const fund = await new Promise((resolve) => {
        db.get('SELECT fund_name FROM funds WHERE fund_code = ?', [tx.fund_code], (err, row) => resolve(err ? null : row));
      });
      enriched.push({ ...tx, fund_name: fund ? fund.fund_name : tx.fund_code });
    }
    // 待确认订单（T+1：SUBMITTED，20:00 按 trade_date 官方净值落账）
    const pendingRows = await new Promise((resolve, reject) => {
      db.all("SELECT id, fund_code, order_type, amount, shares, price, fee, status, order_date, trade_date, reason FROM orders WHERE user_id = ? AND status = 'SUBMITTED' ORDER BY id DESC", [userId], (err, rows) => err ? reject(err) : resolve(rows || []));
    });
    const pending = [];
    for (const p of pendingRows) {
      const fund = await new Promise((resolve) => {
        db.get('SELECT fund_name FROM funds WHERE fund_code = ?', [p.fund_code], (err, row) => resolve(err ? null : row));
      });
      pending.push({ ...p, fund_name: fund ? fund.fund_name : p.fund_code });
    }
    res.json({ list: enriched, pending });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

"""
assert s.count(old) == 1
s = s.replace(old, '// /api/ai/transactions 已抽到 routes/ai.js\n')
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)

# 2) ai.js 加 discover-watchlist 路由
p2 = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\routes\ai.js"
with io.open(p2, 'r', encoding='utf-8') as f:
    s2 = f.read()
old2 = " * ctx: { db, getUserPortfolio, getCurrentUser, getLocalDateStr, userConfigs, buildHotspots }"
new2 = " * ctx: { db, getUserPortfolio, getCurrentUser, getLocalDateStr, userConfigs, buildHotspots, aiDiscoverWatchlist, getWatchlist }"
assert s2.count(old2) == 1
s2 = s2.replace(old2, new2)

old3 = "  const { db, getUserPortfolio, getCurrentUser, getLocalDateStr, userConfigs, buildHotspots } = ctx;"
new3 = "  const { db, getUserPortfolio, getCurrentUser, getLocalDateStr, userConfigs, buildHotspots, aiDiscoverWatchlist, getWatchlist } = ctx;"
assert s2.count(old3) == 1
s2 = s2.replace(old3, new3)

old4 = "  // 市场热点分析"
new4 = """  // AI 按用户性格自主选基进观察池
  r.post('/discover-watchlist', async (req, res) => {
    try {
      const userId = (req.body && req.body.user_id) || getCurrentUser();
      if (!userConfigs[userId]) return res.status(404).json({ error: '用户不存在' });
      const result = await aiDiscoverWatchlist(userId);
      const list = await getWatchlist(userId);
      res.json({
        message: `AI已按${userConfigs[userId].style}维护观察池：新增 ${result.inserted.length} 只，自动调整 ${result.removed} 只`,
        inserted: result.inserted,
        removed: result.removed,
        watchlist: list
      });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  // 市场热点分析"""
assert s2.count(old4) == 1
s2 = s2.replace(old4, new4)
with io.open(p2, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s2)

# 3) server.js 挂载 ai 路由 ctx 加 aiDiscoverWatchlist + getWatchlist
p3 = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p3, 'r', encoding='utf-8') as f:
    s3 = f.read()
old_mount = "app.use('/api/ai', require('./routes/ai')({ db, getUserPortfolio, getCurrentUser, getLocalDateStr, userConfigs, buildHotspots }));"
new_mount = "app.use('/api/ai', require('./routes/ai')({ db, getUserPortfolio, getCurrentUser, getLocalDateStr, userConfigs, buildHotspots, aiDiscoverWatchlist, getWatchlist }));"
assert s3.count(old_mount) == 1
s3 = s3.replace(old_mount, new_mount)
with io.open(p3, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s3)
print('transactions dedup + discover-watchlist moved')
