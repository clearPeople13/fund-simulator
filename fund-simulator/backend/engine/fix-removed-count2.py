# -*- coding: utf-8 -*-
import io
p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js'
c = io.open(p, encoding='utf-8').read()
old = "  const removedCount = await new Promise((resolve, reject) => {\n    db.run(\"DELETE FROM watchlist WHERE user_id = ? AND source = 'ai'\", [userId], (err) => err ? reject(err) : resolve());\n  });"
new = "  const removedCount = await new Promise((resolve, reject) => {\n    db.run(\"DELETE FROM watchlist WHERE user_id = ? AND source = 'ai'\", [userId], function (err) {\n      if (err) reject(err); else resolve(this.changes || 0);\n    });\n  });"
assert c.count(old) == 1, c.count(old)
c = c.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
