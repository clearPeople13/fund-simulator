import io

# 1) server.js 删 /api/ai/results 块
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()
old = """// 获取AI分析结果
app.get('/api/ai/results', async (req, res) => {
  try {
    const userId = req.query.user_id || currentUser;
    const results = await getAnalysisResults(userId);
    
    res.json({
      results: results,
      lastAnalysis: aiAnalysisStatus.lastAnalysis
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

"""
assert s.count(old) == 1
s = s.replace(old, '// /api/ai/results 已抽到 routes/system.js\n')

# 2) system 路由挂载 ctx 加 getAnalysisResults + getCurrentUser
old_mount = "app.use('/api', require('./routes/system')({ aiAnalysisStatus, aiBus, isTradingDay }));"
new_mount = "app.use('/api', require('./routes/system')({ aiAnalysisStatus, aiBus, isTradingDay, getAnalysisResults, getCurrentUser }));"
assert s.count(old_mount) == 1
s = s.replace(old_mount, new_mount)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('ai/results moved to system.js')
