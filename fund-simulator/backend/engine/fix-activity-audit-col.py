# -*- coding: utf-8 -*-
"""修正 activity：audit_logs 无 user_id 列，只按 target LIKE 过滤"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """    const audits = await all("SELECT actor, action, target, detail, created_at FROM audit_logs WHERE user_id = ? OR target LIKE ? ORDER BY created_at DESC LIMIT 6", [userId, '%' + userId + '%']);"""
new = """    const audits = await all("SELECT actor, action, target, detail, created_at FROM audit_logs WHERE target LIKE ? ORDER BY created_at DESC LIMIT 6", ['%' + userId + '%']);"""
assert s.count(old) == 1, 'block not found'
s = s.replace(old, new)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('server.js patched')
