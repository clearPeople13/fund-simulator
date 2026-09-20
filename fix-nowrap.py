import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\App.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()
old = '''.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1400px;
  margin: 0 auto;
  gap: 16px;
  padding: 12px 0;
}'''
new = '''.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1400px;
  margin: 0 auto;
  gap: 16px;
  padding: 12px 0;
  flex-wrap: nowrap;
}'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('flex-wrap: nowrap added')
