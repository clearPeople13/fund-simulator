import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\backend\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = '''  // 启动时 AI 为所有用户按性格自动选基（观察池自主维护，无需用户操作）
  setTimeout(() => {
    autoDiscoverOnStartup();
  }, 2000);'''
new = '''  // 启动时 AI 为所有用户按性格自动选基（观察池自主维护，无需用户操作）
  // 暂时禁用：全流程会阻塞事件循环导致页面打不开
  // setTimeout(() => {
  //   autoDiscoverOnStartup();
  // }, 2000);'''
assert s.count(old) == 1
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('startup auto discover disabled')
