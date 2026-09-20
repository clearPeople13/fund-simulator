# -*- coding: utf-8 -*-
"""AI 实时日志流：
1) 顶部加 aiBus EventEmitter + logAi(type, payload) helper
2) SSE 端点 GET /api/ai/stream
3) performAnalysis 关键节点埋 logAi
"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) 顶部：express 后加 aiBus
old1 = """const app = express();"""
new1 = """const app = express();
const { EventEmitter } = require('events');
// AI 实时日志总线：关键决策节点通过它广播，/api/ai/stream (SSE) 推给前端
const aiBus = new EventEmitter();
aiBus.setMaxListeners(50);
function logAi(type, payload = {}) {
  const evt = { time: new Date().toISOString(), type, ...payload };
  aiBus.emit('ai-log', evt);
  return evt;
}"""
assert s.count(old1) == 1, 'anchor1'
s = s.replace(old1, new1)

# 2) SSE 端点（加在 /api/scheduler/status 前）
old2 = """app.get('/api/scheduler/status', (req, res) => {"""
new2 = """// AI 实时日志流（SSE）：前端 EventSource 订阅，AI 思考/分析/下单时实时推送
app.get('/api/ai/stream', (req, res) => {
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

app.get('/api/scheduler/status', (req, res) => {"""
assert s.count(old2) == 1, 'anchor2'
s = s.replace(old2, new2)

# 3) performAnalysis 开始埋点
old3 = """  console.log(`\\n=== ${typeNames[analysisType]}开始 ===`);
  console.log(`时间: ${new Date().toLocaleString('zh-CN')}`);"""
new3 = """  logAi('phase', { phase: 'start', message: `${typeNames[analysisType]}开始` });
  console.log(`\\n=== ${typeNames[analysisType]}开始 ===`);
  console.log(`时间: ${new Date().toLocaleString('zh-CN')}`);"""
assert s.count(old3) == 1, 'anchor3'
s = s.replace(old3, new3)

# 4) 观察池扫描埋点
old4 = """      console.log(`分析观察池: ${fundList.join(', ')}`);"""
new4 = """      console.log(`分析观察池: ${fundList.join(', ')}`);
      logAi('watchlist', { user: (userConfigs[userId]||{}).name || userId, count: fundList.length, message: `${(userConfigs[userId]||{}).name||userId} 开始分析观察池 ${fundList.length} 只` });"""
assert s.count(old4) == 1, 'anchor4'
s = s.replace(old4, new4)

# 5) 每只基金信号埋点（HOLD/观察）
old5 = """        const decision = (action === 'buy' || action === 'add') ? 'BUY' : 'HOLD';
        const confidence = action === 'buy' ? '高' : (action === 'add' ? '中' : '低');"""
new5 = """        const decision = (action === 'buy' || action === 'add') ? 'BUY' : 'HOLD';
        const confidence = action === 'buy' ? '高' : (action === 'add' ? '中' : '低');
        logAi('signal', { user: (userConfigs[userId]||{}).name || userId, code: fundCode, action, decision, confidence, nav: currentNav, dailyReturn: dailyReturn.toFixed(2), message: `${fundCode} 信号=${action}（置信度${confidence}） 日涨跌${dailyReturn.toFixed(2)}% → ${decision}` });"""
assert s.count(old5) == 1, 'anchor5'
s = s.replace(old5, new5)

# 6) 下单成功埋点
old6 = """                    console.log(`  → 生成建仓订单#${order.id} ${fundCode} ¥${suggestAmount2}（T+1确认）`);"""
new6 = """                    console.log(`  → 生成建仓订单#${order.id} ${fundCode} ¥${suggestAmount2}（T+1确认）`);
                    logAi('order', { user: (userConfigs[userId]||{}).name || userId, code: fundCode, action: 'BUY', amount: suggestAmount2, orderId: order.id, message: `📈 建仓订单#${order.id} ${fundCode} ¥${suggestAmount2}` });"""
assert s.count(old6) == 1, 'anchor6'
s = s.replace(old6, new6)

# 7) 风控拦截埋点
old7 = """                    console.log(`  → 风控拦截买入 ${fundCode}: ${rc.reason}`);"""
new7 = """                    console.log(`  → 风控拦截买入 ${fundCode}: ${rc.reason}`);
                    logAi('block', { user: (userConfigs[userId]||{}).name || userId, code: fundCode, message: `🚫 风控拦截 ${fundCode}: ${rc.reason}` });"""
assert s.count(old7) == 1, 'anchor7'
s = s.replace(old7, new7)

# 8) AI 选基新增埋点
old8 = """        if (discover.inserted.length > 0) {
          console.log(`[AI自动选基] ${userConfigs[userId].name} 新增观察: ${discover.inserted.join(', ')}`);
        }"""
new8 = """        if (discover.inserted.length > 0) {
          console.log(`[AI自动选基] ${userConfigs[userId].name} 新增观察: ${discover.inserted.join(', ')}`);
          logAi('discover', { user: userConfigs[userId].name, codes: discover.inserted, message: `🔍 AI 自主选基新增观察: ${discover.inserted.join(', ')}` });
        }"""
assert s.count(old8) == 1, 'anchor8'
s = s.replace(old8, new8)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('SSE + logAi patched')
