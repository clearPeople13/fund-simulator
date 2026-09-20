import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\backend\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = "const db = new sqlite3.Database('./fund_simulator.db'"
new = "const db = new sqlite3.Database(require('path').join(__dirname, 'fund_simulator.db')"
assert s.count(old) == 1
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('db path changed to absolute')
