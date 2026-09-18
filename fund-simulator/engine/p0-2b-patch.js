// P0-2b: 加 POST /api/scheduler/run（仅本机调试触发周期任务）
const fs = require('fs');
const p = 'C:/Users/jiancent/WorkBuddy/fund/fund-simulator/server.js';
let s = fs.readFileSync(p, 'utf8');
const fail = (m) => { console.error('FAIL: ' + m); process.exit(1); };

const anchor = "app.get('/api/risk/events', (req, res) => {";
if (!s.includes(anchor)) fail('锚点未找到');
const apis = `app.post('/api/scheduler/run', async (req, res) => {
  // 仅本机调试/测试用：手动触发周期任务（设计文档 §7）
  const type = (req.query.type || req.body.type || 'close').toLowerCase();
  const allowed = ['close', 'realtime', 'pre_close', 'confirm'];
  if (!allowed.includes(type)) {
    return res.status(400).json({ error: 'type 仅支持: ' + allowed.join(',') });
  }
  try {
    if (type === 'confirm') {
      const r = await confirmPendingOrders({ db, saveTransaction, updateHolding, audit });
      res.json({ ok: true, type, confirmed: r.confirmed, errors: r.errors });
    } else {
      const started = new Date().toISOString();
      await performAnalysis(type);
      const finished = new Date().toISOString();
      db.run(\`INSERT INTO scheduler_runs (run_type, started_at, finished_at, status, summary) VALUES (?, ?, ?, 'done', ?)\`,
        [type, started, finished, 'manual trigger'], (err) => { if (err) console.error('scheduler_runs 写入失败:', err.message); });
      res.json({ ok: true, type, started, finished });
    }
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

app.get('/api/risk/events', (req, res) => {`;
s = s.replace(anchor, apis);
fs.writeFileSync(p, s, 'utf8');
console.log('scheduler/run API 已添加');
