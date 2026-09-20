import io

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()
old = """// AI 按当前用户性格自主选基进观察池（只读系统：只影响观察池，不涉及任何交易）
app.post('/api/ai/discover-watchlist', async (req, res) => {
  try {
    const userId = (req.body && req.body.user_id) || currentUser;
    if (!userConfigs[userId]) return res.status(404).json({ error: '用户不存在' });
    const result = await aiDiscoverWatchlist(userId);
    const list = await getWatchlist(userId);
    res.json({
      message: `AI已按${userConfigs[userId].style}维护观察池：新增 ${result.inserted.length} 只，自动调整 ${result.removed} 只`,
      inserted: result.inserted,
      removed: result.removed,
      watchlist: list
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

"""
assert s.count(old) == 1
s = s.replace(old, '// /api/ai/discover-watchlist 已抽到 routes/ai.js\n')
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('duplicate discover-watchlist removed')
