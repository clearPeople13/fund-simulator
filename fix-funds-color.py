import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Funds.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()
# 红涨绿跌（A 股习惯）
s = s.replace(
  ".rank-fill.up { background: linear-gradient(90deg, rgba(52,211,153,0.4), #34d399); }",
  ".rank-fill.up { background: linear-gradient(90deg, rgba(248,113,113,0.4), #f87171); }"
)
s = s.replace(
  ".rank-fill.down { background: linear-gradient(90deg, #f87171, rgba(248,113,113,0.4)); }",
  ".rank-fill.down { background: linear-gradient(90deg, #34d399, rgba(52,211,153,0.4)); }"
)
s = s.replace(".profit {\n  color: #34d399;", ".profit {\n  color: #f87171;")
s = s.replace(".loss {\n  color: #f87171;", ".loss {\n  color: #34d399;")
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Funds.vue colors fixed')
