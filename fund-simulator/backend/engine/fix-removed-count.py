# -*- coding: utf-8 -*-
import io
p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js'
c = io.open(p, encoding='utf-8').read()
old = "      message: `AI已按${userConfigs[userId].style}维护观察池：新增 ${result.inserted.length} 只，自动调整 ${result.removed.length} 只`,"
new = "      message: `AI已按${userConfigs[userId].style}维护观察池：新增 ${result.inserted.length} 只，自动调整 ${result.removed} 只`,"
assert c.count(old) == 1
c = c.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
