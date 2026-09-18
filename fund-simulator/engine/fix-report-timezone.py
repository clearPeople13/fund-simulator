# -*- coding: utf-8 -*-
"""报告内容里的 UTC 时间转本地显示"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) 在 getLocalDateStr 之后加 utcToLocalStr
anchor = """function getLocalDateStr(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}"""
add = anchor + """

// SQLite CURRENT_TIMESTAMP 存 UTC（无时区标记）→ 转本地时间串（YYYY-MM-DD HH:mm:ss）
function utcToLocalStr(utcStr) {
  try {
    const d = new Date(String(utcStr).replace(' ', 'T') + 'Z');
    if (isNaN(d.getTime())) return utcStr;
    const p = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
  } catch {
    return utcStr;
  }
}"""
assert s.count(anchor) == 1, 'anchor not found'
s = s.replace(anchor, add)

# 2) 报告内容里风控事件时间转本地
old = """  for (const ev of events) lines.push(`- [${ev.event_type}] ${ev.fund_code || ''} ${ev.detail}（${ev.created_at}）`);"""
new = """  for (const ev of events) lines.push(`- [${ev.event_type}] ${ev.fund_code || ''} ${ev.detail}（${utcToLocalStr(ev.created_at)}）`);"""
assert s.count(old) == 1, 'events line not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('patched server.js')
