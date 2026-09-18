# -*- coding: utf-8 -*-
import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()
old = """    await new Promise((resolve) => {
      await new Promise((resolve) => {
        db.run("DELETE FROM reports WHERE user_id = ? AND report_type = 'daily' AND period = ?", [userId, dateStr], (err) => {
          db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, 'daily', dateStr, content], (err2) => resolve());
        });
      });
    });"""
new = """    await new Promise((resolve) => {
      db.run("DELETE FROM reports WHERE user_id = ? AND report_type = 'daily' AND period = ?", [userId, dateStr], (err) => {
        db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, 'daily', dateStr, content], (err2) => resolve());
      });
    });"""
assert s.count(old) == 1, 'daily block'
s = s.replace(old, new)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('daily flattened')
