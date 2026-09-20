import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Funds.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) 列宽
s = s.replace(
  "{ title: '基金名称', dataIndex: 'fund_name', key: 'fund_name' },",
  "{ title: '基金名称', dataIndex: 'fund_name', key: 'fund_name', width: 240 },"
)
# 2) .fund-name 横向
s = s.replace(
  ".fund-name {\n  color: #a5b4fc;\n  font-weight: 500;\n  cursor: pointer;\n  transition: color 0.2s;\n}",
  ".fund-name {\n  color: #a5b4fc;\n  font-weight: 500;\n  cursor: pointer;\n  transition: color 0.2s;\n  white-space: normal;\n  word-break: normal;\n  line-height: 1.4;\n  display: inline-block;\n}"
)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Funds.vue name fixed')
