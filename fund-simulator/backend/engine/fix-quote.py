# -*- coding: utf-8 -*-
import io
p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js'
c = io.open(p, encoding='utf-8').read()
old = "      db.run('INSERT OR IGNORE INTO watchlist (user_id, fund_code, reason, source) VALUES (?, ?, ?, 'ai')',"
new = "      db.run(\"INSERT OR IGNORE INTO watchlist (user_id, fund_code, reason, source) VALUES (?, ?, ?, 'ai')\","
assert c.count(old) == 1, 'count=%d' % c.count(old)
c = c.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
