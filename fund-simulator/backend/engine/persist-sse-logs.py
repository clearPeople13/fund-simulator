# -*- coding: utf-8 -*-
"""logAi 同时落库：新建 ai_event_logs 表，所有 SSE 事件持久化留档"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) 建表（在现有 CREATE TABLE 附近找位置）——直接在 aiBus 定义后建表
old1 = """function logAi(type, payload = {}) {
  const evt = { time: new Date().toISOString(), type, ...payload };
  aiBus.emit('ai-log', evt);
  return evt;
}"""
new1 = """function logAi(type, payload = {}) {
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
assert s.count(old1) == 1, 'logAi not found'
s = s.replace(old1, new1)

# 2) 建表语句（在 scheduler_runs 建表附近）
old2 = """    db.run(`CREATE TABLE IF NOT EXISTS scheduler_runs ("""
new2 = """    db.run(`CREATE TABLE IF NOT EXISTS ai_event_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      event_type TEXT,
      user_name TEXT,
      message TEXT,
      detail TEXT,
      event_time DATETIME
    )`)
    db.run(`CREATE TABLE IF NOT EXISTS scheduler_runs ("""
assert s.count(old2) == 1, 'scheduler_runs not found'
s = s.replace(old2, new2)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('ai_event_logs persisted')
