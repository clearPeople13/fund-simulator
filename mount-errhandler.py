import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()
old = """// 启动服务器
app.listen(PORT, () => {"""
new = """// 统一错误处理中间件（必须最后挂）
app.use(errorHandler);

// 启动服务器
app.listen(PORT, () => {"""
assert s.count(old) == 1
s = s.replace(old, new)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('errorHandler mounted')
