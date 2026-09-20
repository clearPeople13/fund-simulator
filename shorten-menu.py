import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\App.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

replacements = [
    ('<span>AI操盘</span>', '<span>首页</span>'),
    ('<span>基金库</span>', '<span>基金</span>'),
    ('<span>市场行情</span>', '<span>行情</span>'),
    ('<span>AI分析</span>', '<span>分析</span>'),
    ('<span>预警中心</span>', '<span>预警</span>'),
    ('<span>报告中心</span>', '<span>报告</span>'),
    ('<span>基金经理</span>', '<span>经理</span>'),
]
for old, new in replacements:
    assert s.count(old) == 1, (old, s.count(old))
    s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('menu shortened')
