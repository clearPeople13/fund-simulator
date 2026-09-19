import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\style.css"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()
# A 股习惯：红涨绿跌（盈利=红，亏损=绿）
s = s.replace(".stat-card .stat-value.up { color: #34d399; }", ".stat-card .stat-value.up { color: #f87171; }")
s = s.replace(".stat-card .stat-value.down { color: #f87171; }", ".stat-card .stat-value.down { color: #34d399; }")
s = s.replace(".profit { color: #34d399 !important; font-weight: 600; }", ".profit { color: #f87171 !important; font-weight: 600; }")
s = s.replace(".loss { color: #f87171 !important; font-weight: 600; }", ".loss { color: #34d399 !important; font-weight: 600; }")
# 加全局 CSS 变量
s = s.replace("  --success: #34d399;", "  --success: #34d399;\n  --up: #f87171;    /* A股涨红 */\n  --down: #34d399;  /* A股跌绿 */")
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('red-up-green-down applied')
