# -*- coding: utf-8 -*-
"""pressure/daily 去重块多余嵌套一层 await，拍平"""
import io

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old2 = """  await new Promise((resolve) => {
    await new Promise((resolve) => {
      db.run("DELETE FROM reports WHERE user_id = ? AND report_type = 'pressure' AND period = ?", [userId, getLocalDateStr()], (err) => {
        db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, 'pressure', getLocalDateStr(), content], (err2) => resolve());
      });"""
new2 = """  await new Promise((resolve) => {
    db.run("DELETE FROM reports WHERE user_id = ? AND report_type = 'pressure' AND period = ?", [userId, getLocalDateStr()], (err) => {
      db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, 'pressure', getLocalDateStr(), content], (err2) => resolve());"""
assert s.count(old2) == 1, 'pressure block'
s = s.replace(old2, new2)

# daily 同样拍平
old3 = """      await new Promise((resolve) => {
        db.run("DELETE FROM reports WHERE user_id = ? AND report_type = 'daily' AND period = ?", [userId, dateStr], (err) => {
          db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, 'daily', dateStr, content], (err2) => resolve());
        });
      });"""
new3 = """      await new Promise((resolve) => {
        db.run("DELETE FROM reports WHERE user_id = ? AND report_type = 'daily' AND period = ?", [userId, dateStr], (err) => {
          db.run('INSERT INTO reports (user_id, report_type, period, content) VALUES (?, ?, ?, ?)', [userId, 'daily', dateStr, content], (err2) => resolve());
        });
      });"""
# daily 已经是单层（1258 那种双重才错），检查实际是否双重
import re
print('daily double-nest present:', 'await new Promise((resolve) => {\n        db.run("DELETE FROM reports WHERE user_id = ? AND report_type = \'daily\'' in s)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('pressure flattened')
