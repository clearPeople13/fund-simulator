import io

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) 删 hotspots 块
old = """app.get('/api/ai/hotspots', async (req, res) => {
  try {
    const userId = req.query.user_id || currentUser;
    if (!userConfigs[userId]) return res.status(404).json({ error: '用户不存在' });
    const data = await buildHotspots(userId);
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

"""
assert s.count(old) == 1
s = s.replace(old, '// /api/ai/hotspots 已抽到 routes/ai.js\n')

# 2) ai 路由挂载 ctx 加 buildHotspots
old_mount = "app.use('/api/ai', require('./routes/ai')({ db, getUserPortfolio, getCurrentUser, getLocalDateStr, userConfigs }));"
new_mount = "app.use('/api/ai', require('./routes/ai')({ db, getUserPortfolio, getCurrentUser, getLocalDateStr, userConfigs, buildHotspots }));"
assert s.count(old_mount) == 1
s = s.replace(old_mount, new_mount)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('hotspots moved')
