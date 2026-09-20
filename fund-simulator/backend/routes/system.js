/**
 * 系统/SSE 路由：/api/ai/status /api/ai/results /api/ai/stream /api/scheduler/status /api/scheduler/run
 * ctx: { aiAnalysisStatus, aiBus, isTradingDay, getAnalysisResults, getCurrentUser,
 *        db, userConfigs, computeFundProfiles, getRiskParams, rebalanceCheck, switchFunds,
 *        generateReport, performanceAttribution, generatePressureReport,
 *        confirmPendingOrders, performAnalysis, saveTransaction, updateHolding, audit }
 */
const { Router } = require('express');

module.exports = function systemRoutes(ctx) {
  const r = Router();
  const { aiAnalysisStatus, aiBus, isTradingDay, getAnalysisResults, getCurrentUser,
          db, userConfigs, computeFundProfiles, getRiskParams, rebalanceCheck, switchFunds,
          generateReport, performanceAttribution, generatePressureReport,
          confirmPendingOrders, performAnalysis, saveTransaction, updateHolding, audit } = ctx;

  r.get('/ai/status', (req, res) => res.json(aiAnalysisStatus));

  r.get('/ai/results', async (req, res) => {
    try {
      const userId = req.query.user_id || getCurrentUser();
      const results = await getAnalysisResults(userId);
      res.json({ results, lastAnalysis: aiAnalysisStatus.lastAnalysis });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.get('/ai/stream', (req, res) => {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no'
    });
    res.write(': connected\n\n');
    const send = (evt) => res.write('data: ' + JSON.stringify(evt) + '\n\n');
    send({ time: new Date().toISOString(), type: 'system', message: 'AI 日志流已连接' });
    const onLog = (evt) => send(evt);
    aiBus.on('ai-log', onLog);
    const heartbeat = setInterval(() => res.write(': hb\n\n'), 25000);
    req.on('close', () => { clearInterval(heartbeat); aiBus.off('ai-log', onLog); });
  });

  r.get('/scheduler/status', (req, res) => {
    res.json({
      trading_day: isTradingDay(new Date()),
      tasks: ['realtime(30min)', 'pre_close(14:30)', 'close(15:00)', 'post_close_confirm(20:00)', 'daily_backup(23:30)']
    });
  });

  r.post('/scheduler/run', async (req, res) => {
    const type = (req.query.type || req.body.type || 'close').toLowerCase();
    const allowed = ['close', 'realtime', 'pre_close', 'confirm', 'weekly', 'monthly'];
    if (!allowed.includes(type)) {
      return res.status(400).json({ error: 'type 仅支持: ' + allowed.join(',') });
    }
    try {
      if (type === 'weekly') {
        await computeFundProfiles();
        const results = [];
        for (const userId of Object.keys(userConfigs)) {
          await getRiskParams(userId);
          let rb = null, sw = null;
          try { rb = await rebalanceCheck(userId); } catch (e) { rb = 'SKIP:' + e.message; }
          try { sw = await switchFunds(userId); } catch (e) { sw = 'SKIP:' + e.message; }
          await generateReport(userId, 'weekly');
          results.push({ userId, rebalance: rb, switch: sw });
        }
        return res.json({ ok: true, type, results });
      }
      if (type === 'monthly') {
        const results = [];
        for (const userId of Object.keys(userConfigs)) {
          const attr = await performanceAttribution(userId);
          await generatePressureReport(userId);
          await generateReport(userId, 'monthly');
          results.push({ userId, attribution: attr });
        }
        return res.json({ ok: true, type, results });
      }
      if (type === 'confirm') {
        const r = await confirmPendingOrders({ db, saveTransaction, updateHolding, audit });
        res.json({ ok: true, type, confirmed: r.confirmed, errors: r.errors });
      } else {
        const started = new Date().toISOString();
        await performAnalysis(type);
        const finished = new Date().toISOString();
        db.run(`INSERT INTO scheduler_runs (run_type, started_at, finished_at, status, summary) VALUES (?, ?, ?, 'done', ?)`,
          [type, started, finished, 'manual trigger'], (err) => { if (err) console.error('scheduler_runs 写入失败:', err.message); });
        res.json({ ok: true, type, started, finished });
      }
    } catch (e) { res.status(500).json({ ok: false, error: e.message }); }
  });

  return r;
};
