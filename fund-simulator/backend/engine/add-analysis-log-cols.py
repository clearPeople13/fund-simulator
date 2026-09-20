# -*- coding: utf-8 -*-
"""analysis_logs 增加 signal_label/signal_reason 列（建表语句 + 旧库 ALTER 兼容）"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """  estimated_pnl REAL,
  analysis_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (fund_code) REFERENCES funds (fund_code)
)`);"""
new = """  estimated_pnl REAL,
  signal_label TEXT,
  signal_reason TEXT,
  analysis_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (fund_code) REFERENCES funds (fund_code)
)`);

// 旧库迁移：analysis_logs 补 signal_label/signal_reason（热点分析记录用）
db.run("ALTER TABLE analysis_logs ADD COLUMN signal_label TEXT", (err) => {});
db.run("ALTER TABLE analysis_logs ADD COLUMN signal_reason TEXT", (err) => {});"""
assert s.count(old) == 1, 'create not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('analysis_logs columns added')
