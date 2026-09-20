import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\App.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 窄屏：logo + 用户切换器一行，菜单第二行
old = '''@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    padding: 12px 0;
    height: auto;
  }

  .logo {
    margin-bottom: 8px;
  }

  .header-menu {
    width: 100%;
    margin-left: 0;
  }

  .header-right {
    margin-top: 8px;
  }
}'''
new = '''@media (max-width: 768px) {
  .header-content {
    flex-wrap: wrap;
    padding: 12px 0;
  }

  .logo {
    flex: 1;
  }

  .header-right {
    flex: 0;
  }

  .header-menu {
    flex-basis: 100%;
    margin-left: 0;
    margin-top: 8px;
  }
}'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('mobile header: logo+user row, menu second row')
