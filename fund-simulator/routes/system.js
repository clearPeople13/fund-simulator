/**
 * 系统/SSE 路由：/api/ai/status /api/ai/stream /api/scheduler/status
 * ctx: { aiAnalysisStatus, aiBus, isTradingDay }
 */
const { Router } = require('express');

module.exports = function systemRoutes(ctx) {
  const r = Router();
  const { aiAnalysisStatus, aiBus, isTradingDay } = ctx;

  r.get('/status', (req, res) => res.json(aiAnalysisStatus));

  r.get('/stream', (req, res) => {
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

  return r;
};
