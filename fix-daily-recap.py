import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\backend\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = '''      // 每日复盘（每日收盘后）
      try { await generateDailyRecap(); } catch (e) { console.error('[复盘] 失败:', e.message); }'''
new = '''      // 每日复盘（仅收盘分析时生成，避免盘中每30分钟重复生成）
      if (analysisType === 'close') {
        try { await generateDailyRecap(); } catch (e) { console.error('[复盘] 失败:', e.message); }
      }'''
assert s.count(old) == 1
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('daily recap only on close analysis')
