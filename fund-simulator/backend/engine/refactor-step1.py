# -*- coding: utf-8 -*-
"""server.js 模块化：时间函数→utils/time，事件总线→events/aiBus"""
import io

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) 顶部 require 替换 aiBus 定义为模块导入
old1 = """const app = express();
const { EventEmitter } = require('events');
// AI 实时日志总线：关键决策节点通过它广播，/api/ai/stream (SSE) 推给前端
const aiBus = new EventEmitter();
aiBus.setMaxListeners(50);
function logAi(type, payload = {}) {
  const evt = { time: new Date().toISOString(), type, ...payload };
  aiBus.emit('ai-log', evt);
  // 落档：所有实时事件存 ai_event_logs（便于事后追溯 AI 思考全过程）
  try {
    db.run('INSERT INTO ai_event_logs (event_type, user_name, message, detail, event_time) VALUES (?, ?, ?, ?, ?)',
      [type, payload.user || '', payload.message || '', JSON.stringify(payload).slice(0, 1500), new Date().toISOString().slice(0, 19)],
      (e) => { if (e) console.error('ai_event_logs 写入失败:', e.message); });
  } catch (e) { /* 表可能还没建 */ }
  return evt;
}"""
new1 = """const app = express();
// 模块化：时间/交易日纯函数、AI 事件总线、统一错误处理（见 CODING_STANDARDS.md）
const { getLocalDateStr, isTradingDay, isMarketOpenNow, nextTradingDay } = require('./utils/time');
const { aiBus, logAi, init: initAiBus } = require('./events/aiBus');
const { errorHandler, asyncHandler } = require('./middleware/errorHandler');"""
assert s.count(old1) == 1, 'top block'
s = s.replace(old1, new1)

# 2) 删除本地时间函数块（1625-1665）
old2 = """// 本地时区日期字符串（YYYY-MM-DD）
function getLocalDateStr(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

// A股休市日（工作日内的法定节假日）：engine/holidays.json（国办发明电〔2025〕7号，2026）
const HOLIDAYS = (() => {
  try {
    return require('./engine/holidays.json');
  } catch {
    return {};
  }
})();

// 是否交易日：周一~周五 且 非节假日（节假日每年 11 月国务院公布后补充 holidays.json）
function isTradingDay(d = new Date()) {
  const dow = d.getDay();
  if (dow === 0 || dow === 6) return false;
  const year = String(d.getFullYear());
  const list = HOLIDAYS[year] || [];
  return list.indexOf(getLocalDateStr(d)) === -1;
}

// 是否正在连续竞价时段（交易日 9:30-11:30 / 13:00-15:00）
function isMarketOpenNow(d = new Date()) {
  if (!isTradingDay(d)) return false;
  const h = d.getHours(), m = d.getMinutes();
  const mins = h * 60 + m;
  return (mins >= 570 && mins <= 690) || (mins >= 780 && mins <= 900); // 9:30=570, 11:30=690, 13:00=780, 15:00=900
}

// 找到不小于 date 的第一个交易日 0 点
function nextTradingDay(date) {
  const d = new Date(date);
  while (!isTradingDay(d)) {
    d.setDate(d.getDate() + 1);
  }
  return d;
}"""
new2 = """// 时间/交易日函数已抽到 utils/time.js（唯一出处）；节假日表由该模块读 engine/holidays.json"""
assert s.count(old2) == 1, 'time block'
s = s.replace(old2, new2)

# 3) db 连接后调 initAiBus(db)
old3 = """const db = new sqlite3.Database('./fund_simulator.db', (err) => {
  if (err) {
    console.error('数据库连接失败:', err.message);
  } else {
    console.log('已连接到SQLite数据库');
    initDatabase();
  }
});"""
new3 = """const db = new sqlite3.Database('./fund_simulator.db', (err) => {
  if (err) {
    console.error('数据库连接失败:', err.message);
  } else {
    console.log('已连接到SQLite数据库');
    initAiBus(db); // AI 事件总线绑定 db，logAi 才能落档
    initDatabase();
  }
});"""
assert s.count(old3) == 1, 'db block'
s = s.replace(old3, new3)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('server.js modularized')
