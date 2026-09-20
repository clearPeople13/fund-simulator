import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) 加 getter/setter
old1 = """// 当前活跃用户
let currentUser = 'default';"""
new1 = """// 当前活跃用户（拆 routes 时用 getter/setter 保持引用）
let currentUser = 'default';
const getCurrentUser = () => currentUser;
const setCurrentUser = (v) => { currentUser = v; };"""
assert s.count(old1) == 1
s = s.replace(old1, new1)

# 2) 删除 /api/users/* 路由块（2866 到 2996 附近）
# 从 app.get('/api/users' 到 r.get('/:id/config' 结束）
start = s.find("app.get('/api/users', async (req, res) => {")
assert start != -1, 'users block start'
# 找结束：app.get('/api/analysis/logs' 之前
end = s.find("app.get('/api/analysis/logs'", start)
assert end != -1, 'users block end'
s = s[:start] + "// /api/users/* 路由已抽到 routes/users.js\n" + s[end:]

# 3) 在 app.listen 前挂载 users 路由
old3 = "// 统一错误处理中间件（必须最后挂）\napp.use(errorHandler);"
new3 = """// 挂载用户路由（从 routes/users.js 注入依赖）
app.use('/api/users', require('./routes/users')({
  db, userConfigs, getCurrentUser, setCurrentUser, getWatchlist, ensureFundWithNav
}));

// 统一错误处理中间件（必须最后挂）
app.use(errorHandler);"""
assert s.count(old3) == 1
s = s.replace(old3, new3)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('users routes extracted, size now:', len(s))
