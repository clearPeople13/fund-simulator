import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\backend\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()
old = "path.join(__dirname, 'frontend/dist')"
new = "path.join(__dirname, '../frontend/dist')"
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('fixed dist path')
