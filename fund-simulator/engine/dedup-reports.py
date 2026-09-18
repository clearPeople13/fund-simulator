# -*- coding: utf-8 -*-
"""reports 去重：三处 INSERT 前先 DELETE 同 (user_id, report_type, period) 旧记录——同周期只留最新一份"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) generateReport（889）
old1 = """    db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, reportType, period, content], (err) => resolve());"""
new1 = """    // 同周期去重：先删同 (user_id, report_type, period) 旧报告，再插入最新——避免手动/调度重复生成堆积
    await new Promise((resolve) => db.run('DELETE FROM reports WHERE user_id = ? AND report_type = ? AND period = ?', [userId, reportType, period], (err) => resolve()));
    db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, reportType, period, content], (err) => resolve());"""
assert s.count(old1) == 1, 'insert1 not found'
s = s.replace(old1, new1)

# 2) pressure（1255）
old2 = """    db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, 'pressure', getLocalDateStr(), content], (err) => resolve());"""
new2 = """    await new Promise((resolve) => db.run("DELETE FROM reports WHERE user_id = ? AND report_type = 'pressure' AND period = ?", [userId, getLocalDateStr()], (err) => resolve()));
    db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, 'pressure', getLocalDateStr(), content], (err) => resolve());"""
assert s.count(old2) == 1, 'insert2 not found'
s = s.replace(old2, new2)

# 3) daily（1304）
old3 = """      db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, 'daily', dateStr, content], (err) => resolve());"""
new3 = """      await new Promise((resolve) => db.run("DELETE FROM reports WHERE user_id = ? AND report_type = 'daily' AND period = ?", [userId, dateStr], (err) => resolve()));
      db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, 'daily', dateStr, content], (err) => resolve());"""
assert s.count(old3) == 1, 'insert3 not found'
s = s.replace(old3, new3)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('dedup inserts patched')
