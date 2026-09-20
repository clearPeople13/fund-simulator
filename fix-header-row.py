import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\App.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 改 .logo 不要居中
old_logo = '''.logo {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  gap: 10px;
  white-space: nowrap;
  flex-shrink: 0;
}'''
new_logo = '''.logo {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  gap: 10px;
  white-space: nowrap;
  flex-shrink: 0;
  margin-right: auto;
}'''
assert s.count(old_logo) == 1
s = s.replace(old_logo, new_logo)

# 改 .header-menu flex: 1
old_menu = '''.header-menu {
  background: transparent !important;
  border: none !important;
  flex: 0 1 auto;
  margin-left: 20px;
  line-height: normal;
  overflow-x: auto;
  overflow-y: hidden;
  white-space: nowrap;
}'''
new_menu = '''.header-menu {
  background: transparent !important;
  border: none !important;
  flex: 1;
  margin-left: 20px;
  line-height: normal;
  overflow-x: auto;
  overflow-y: hidden;
  white-space: nowrap;
}'''
assert s.count(old_menu) == 1
s = s.replace(old_menu, new_menu)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('logo margin-right:auto + menu flex:1')
