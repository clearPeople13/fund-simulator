import io

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) 删 /api/ai/analyze 块
start = s.find("// 触发AI分析\napp.post('/api/ai/analyze'")
end = s.find("// AI 按当前用户性格自主选基进观察池", start)
assert start != -1 and end != -1
s = s[:start] + "// /api/ai/analyze 已抽到 routes/ai.js\n" + s[end:]

# 2) ai 路由挂载 ctx 加新依赖
old_mount = "app.use('/api/ai', require('./routes/ai')({ db, getUserPortfolio, getCurrentUser, getLocalDateStr, userConfigs, buildHotspots, aiDiscoverWatchlist, getWatchlist }));"
new_mount = "app.use('/api/ai', require('./routes/ai')({ db, getUserPortfolio, getCurrentUser, getLocalDateStr, userConfigs, buildHotspots, aiDiscoverWatchlist, getWatchlist, getUserWatchlistCodes, aiAnalysisStatus, aiAnalysisResults, getFundSignal, saveAnalysisResult }));"
assert s.count(old_mount) == 1
s = s.replace(old_mount, new_mount)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('analyze moved')
