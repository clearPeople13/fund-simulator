# -*- coding: utf-8 -*-
import io
p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\data-fetcher.js'
c = io.open(p, encoding='utf-8').read()
old = "const etf = DataFetcher.ETF_PROXY_MAP[fundCode];"
new = "const etf = FundDataFetcher.ETF_PROXY_MAP[fundCode];"
assert c.count(old) == 1
c = c.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
