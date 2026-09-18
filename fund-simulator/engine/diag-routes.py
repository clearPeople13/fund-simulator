# -*- coding: utf-8 -*-
import io
c = io.open(r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\api\routes.js', encoding='utf-8').read()
seg = "router.get('/funds/:code', (req, res) => {"
print('seg1 count', c.count(seg))
i = c.find(seg)
print(repr(c[i:i+400]))
