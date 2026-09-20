import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = ".data-table .name { font-weight: 500; color: var(--text); }"
new = ".data-table .name { font-weight: 500; color: var(--text); white-space: normal; min-width: 140px; max-width: 200px; line-height: 1.4; }"
assert s.count(old) == 1
s = s.replace(old, new)

# 表格紧凑些
old2 = ".data-table {\n  width: 100%;\n  border-collapse: collapse;\n  font-size: 14px;\n}"
new2 = ".data-table {\n  width: 100%;\n  border-collapse: collapse;\n  font-size: 13px;\n}"
assert s.count(old2) == 1
s = s.replace(old2, new2)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('table name fixed')
