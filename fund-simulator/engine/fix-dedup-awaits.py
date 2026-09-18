# -*- coding: utf-8 -*-
"""修正三处去重：嵌套 await 改为 db.run 回调链"""
import io

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old1 = """  await new Promise((resolve) => {
    // 同周期去重：先删同 (user_id, report_type, period) 旧报告，再插入最新——避免手动/调度重复生成堆积
    await new Promise((resolve) => db.run('DELETE FROM reports WHERE user_id = ? AND report_type = ? AND period = ?', [userId, reportType, period], (err) => resolve()));
    db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, reportType, period, content], (err) => resolve());
  });"""
new1 = """  await new Promise((resolve) => {
    // 同周期去重：先删同 (user_id, report_type, period) 旧报告，再插入最新——避免手动/调度重复生成堆积
    db.run('DELETE FROM reports WHERE user_id = ? AND report_type = ? AND period = ?', [userId, reportType, period], (err) => {
      db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, reportType, period, content], (err2) => resolve());
    });
  });"""
assert s.count(old1) == 1, 'block1'
s = s.replace(old1, new1)

# pressure / daily 两处：检查是否也嵌在 await Promise 里——把那两个 await 也改成回调链
old2 = """    await new Promise((resolve) => db.run("DELETE FROM reports WHERE user_id = ? AND report_type = 'pressure' AND period = ?", [userId, getLocalDateStr()], (err) => resolve()));
    db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, 'pressure', getLocalDateStr(), content], (err) => resolve());"""
new2 = """    await new Promise((resolve) => {
      db.run("DELETE FROM reports WHERE user_id = ? AND report_type = 'pressure' AND period = ?", [userId, getLocalDateStr()], (err) => {
        db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, 'pressure', getLocalDateStr(), content], (err2) => resolve());
      });
    });"""
if s.count(old2) == 1:
    s = s.replace(old2, new2); print('pressure fixed')
else:
    print('pressure already chain?')

old3 = """      await new Promise((resolve) => db.run("DELETE FROM reports WHERE user_id = ? AND report_type = 'daily' AND period = ?", [userId, dateStr], (err) => resolve()));
      db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, 'daily', dateStr, content], (err) => resolve());"""
new3 = """      await new Promise((resolve) => {
        db.run("DELETE FROM reports WHERE user_id = ? AND report_type = 'daily' AND period = ?", [userId, dateStr], (err) => {
          db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, 'daily', dateStr, content], (err2) => resolve());
        });
      });"""
if s.count(old3) == 1:
    s = s.replace(old3, new3); print('daily fixed')
else:
    print('daily already chain?')

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('done')
