import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\backend\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = '''    console.log(`\\n=== ${typeNames[analysisType]}完成 ===\\n`);'''
new = '''    console.log(`\\n=== ${typeNames[analysisType]}完成 ===\\n`);
    // 飞书通知：AI 分析完成
    try {
      const { sendFeishu } = require('./notify');
      const typeName = { realtime: '实时分析', pre_close: '收盘前分析', close: '收盘分析' }[analysisType] || analysisType;
      sendFeishu('AI' + typeName + '完成', new Date().toLocaleString('zh-CN') + ' ' + typeName + '已完成，见分析页');
    } catch (e) { console.error('[飞书] 分析通知失败: ' + e.message); }'''
assert s.count(old) == 1
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('analysis complete feishu notification added')
