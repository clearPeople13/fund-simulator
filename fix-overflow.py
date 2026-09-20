import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\App.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()
old = ':overflowed-indicator="null"'
new = ':overflowed-indicator="\'更多\'"'
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('overflowed-indicator set to 更多')
