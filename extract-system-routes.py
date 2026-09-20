import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) 删 /api/ai/status
old1 = """// 获取AI分析状态
app.get('/api/ai/status', (req, res) => {
  res.json(aiAnalysisStatus);
});

"""
assert s.count(old1) == 1
s = s.replace(old1, '// /api/ai/status 已抽到 routes/system.js\n')

# 2) 删 /api/ai/stream
old2 = """app.get('/api/ai/stream', (req, res) => {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'X-Accel-Buffering': 'no'
  });
  res.write(': connected\\n\\n');
  const send = (evt) => res.write('data: ' + JSON.stringify(evt) + '\\n\\n');
  send({ time: new Date().toISOString(), type: 'system', message: 'AI 日志流已连接' });
  const onLog = (evt) => send(evt);
  aiBus.on('ai-log', onLog);
  const heartbeat = setInterval(() => res.write(': hb\\n\\n'), 25000);
  req.on('close', () => { clearInterval(heartbeat); aiBus.off('ai-log', onLog); });
});

"""
assert s.count(old2) == 1
s = s.replace(old2, '// /api/ai/stream 已抽到 routes/system.js\n')

# 3) 删 /api/scheduler/status
old3 = """app.get('/api/scheduler/status', (req, res) => {
  res.json({
    trading_day: isTradingDay(new Date()),
    tasks: ['realtime(30min)', 'pre_close(14:30)', 'close(15:00)', 'post_close_confirm(20:00)', 'daily_backup(23:30)']
  });
});

"""
assert s.count(old3) == 1
s = s.replace(old3, '// /api/scheduler/status 已抽到 routes/system.js\n')

# 4) 挂载 system 路由
old4 = "// 挂载只读查询路由（必须在 SPA fallback 之前）"
new4 = """// 挂载系统/SSE 路由（必须在 SPA fallback 之前）
app.use('/api', require('./routes/system')({ aiAnalysisStatus, aiBus, isTradingDay }));

// 挂载只读查询路由（必须在 SPA fallback 之前）"""
assert s.count(old4) == 1
s = s.replace(old4, new4)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('system routes extracted, size:', len(s))
