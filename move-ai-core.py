import io

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) 删 portfolio + compare + transactions 三个块
# portfolio: 从 "// 获取AI持仓" 到 "// 双 AI 基金经理经营对比"
start1 = s.find("// 获取AI持仓\napp.get('/api/ai/portfolio'")
end1 = s.find("// 单基金每日收益明细", start1)
assert start1 != -1 and end1 != -1
s = s[:start1] + "// /api/ai/portfolio + /api/ai/compare + /api/ai/transactions 已抽到 routes/ai.js\n" + s[end1:]

# 2) 挂载 ai 路由
old_mount = "// 挂载系统/SSE 路由（必须在 SPA fallback 之前）"
new_mount = """// 挂载 AI 核心路由（必须在 SPA fallback 之前）
app.use('/api/ai', require('./routes/ai')({ db, getUserPortfolio, getCurrentUser, getLocalDateStr, userConfigs }));

// 挂载系统/SSE 路由（必须在 SPA fallback 之前）"""
assert s.count(old_mount) == 1
s = s.replace(old_mount, new_mount)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('portfolio+compare+transactions moved, size:', len(s))
