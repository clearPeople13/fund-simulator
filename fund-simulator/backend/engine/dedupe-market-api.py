# -*- coding: utf-8 -*-
"""删除 server.js 中重复的 /api/market/overview 旧块（用 all 的版本），保留 qall 版本"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 统计出现次数
print('overview 出现次数:', s.count("app.get('/api/market/overview'"))
print('all( 出现次数(overview块内):', s.count('await all("SELECT date'))

# 精确删除：从第一个 "// 市场行情概览" 到第一个 "});\n\n// 市场行情概览" 之间的旧块
start_marker = "// 市场行情概览：基准指数走势 + 市场温度 + 全市场基金涨跌统计\napp.get('/api/market/overview', async (req, res) => {\n  try {"
end_marker = "});\n\n// 市场行情概览：基准指数走势 + 市场温度 + 全市场基金涨跌统计"
i = s.find(start_marker)
j = s.find(end_marker, i)
if i != -1 and j != -1:
    j += len("});")
    removed = s[i:j]
    s = s[:i] + s[j:]
    print('已删除旧块，长度:', len(removed))
else:
    print('标记未找到', i, j)
    raise SystemExit(1)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('overview 剩余出现次数:', s.count("app.get('/api/market/overview'"))
