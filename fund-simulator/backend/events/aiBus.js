/**
 * AI 事件总线（观察者模式单例）
 * - SSE 端点订阅它实现实时推送
 * - logAi() 统一日志出口：console + SSE + ai_event_logs 落档
 * db 通过 init(db) 注入，避免循环依赖
 */
const { EventEmitter } = require('events');

const aiBus = new EventEmitter();
aiBus.setMaxListeners(50);

let _db = null;
function init(db) { _db = db; }

/** 统一 AI 日志入口：广播 + 落档 */
function logAi(type, payload = {}) {
  const evt = { time: new Date().toISOString(), type, ...payload };
  aiBus.emit('ai-log', evt);
  if (_db) {
    _db.run('INSERT INTO ai_event_logs (event_type, user_name, message, detail, event_time) VALUES (?, ?, ?, ?, ?)',
      [type, payload.user || '', payload.message || '', JSON.stringify(payload).slice(0, 1500),
       new Date().toISOString().slice(0, 19)],
      (e) => { if (e) console.error('ai_event_logs 写入失败:', e.message); });
  }
  return evt;
}

module.exports = { aiBus, init, logAi };
