import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """// 其他请求兜底返回 Vue index.html
app.use((req, res) => {
  res.sendFile(path.join(__dirname, 'frontend/dist', 'index.html'));
});

// 挂载用户路由（从 routes/users.js 注入依赖）
app.use('/api/users', require('./routes/users')({
  db, userConfigs, getCurrentUser, setCurrentUser, getWatchlist, ensureFundWithNav
}));

// 统一错误处理中间件（必须最后挂）
app.use(errorHandler);"""
new = """// 挂载用户路由（必须在 SPA fallback 之前）
app.use('/api/users', require('./routes/users')({
  db, userConfigs, getCurrentUser, setCurrentUser, getWatchlist, ensureFundWithNav
}));

// 其他请求兜底返回 Vue index.html
app.use((req, res) => {
  res.sendFile(path.join(__dirname, 'frontend/dist', 'index.html'));
});

// 统一错误处理中间件（必须最后挂）
app.use(errorHandler);"""
assert s.count(old) == 1
s = s.replace(old, new)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('route order fixed')
