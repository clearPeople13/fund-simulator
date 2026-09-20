# -*- coding: utf-8 -*-
import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Portfolio.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()
old = "每日实际盈亏，红涨绿跌（支付宝收益日历样式）"
new = "每日实际盈亏，涨绿跌红（按持仓份额 × 净值变动口径）"
assert s.count(old) == 1
s = s.replace(old, new)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('calendar tag fixed')
