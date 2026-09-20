import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\backend\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()
old = """// Vue Router history 模式 + 前端生产构建静态文件（与 server-production.js 一致）
app.use(history());
app.use(express.static(path.join(__dirname, 'frontend/dist')));

// 静态文件服务（放在API路由之后）
app.use(express.static('public'));

// 挂载 AI 核心路由（必须在 SPA fallback 之前）"""
new = """// Vue Router history 模式 + 前端生产构建静态文件
app.use(history());
app.use(express.static(path.join(__dirname, 'frontend/dist')));

// 挂载 AI 核心路由（必须在 SPA fallback 之前）"""
assert s.count(old) == 1
s = s.replace(old, new)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('removed express.static(public)')
