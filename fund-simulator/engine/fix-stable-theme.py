# -*- coding: utf-8 -*-
import io
p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js'
c = io.open(p, encoding='utf-8').read()
old = "      if ((f.fund_type === '指数型' || (f.fund_type === '混合型' && !theme && r1y < 40))) matched = true;"
new = "      if ((f.fund_type === '指数型' && !theme) || (f.fund_type === '混合型' && !theme && r1y < 40)) matched = true;"
assert c.count(old) == 1
c = c.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
