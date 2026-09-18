# -*- coding: utf-8 -*-
import io
p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js'
c = io.open(p, encoding='utf-8').read()
old = "const THEME_RE = /新能源|白酒|能源|成长|消费|科技|军工|医药|互联网|半导体|芯片|数字|人工智能|创新|制造|改革|新兴/;"
new = "const THEME_RE = /新能源|白酒|能源|成长|消费|科技|军工|医药|互联网|半导体|芯片|集成电路|数字|人工智能|创新|制造|改革|新兴|软件|传媒|游戏|化工|有色|农业|电子|通信|计算机|机器人|高端装备/;"
assert c.count(old) == 1
c = c.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
