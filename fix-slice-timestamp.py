import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\backend\routes\ai.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 修复：transaction_date 现在是时间戳（整数），不能用 .slice
old = "        const pending = !!(lastBuy && lastBuy.md && lastBuy.md.slice(0, 10) === todayStr);"
new = """        // transaction_date 现在是时间戳（毫秒），转成日期字符串比较
        let pending = false;
        if (lastBuy && lastBuy.md) {
          const md = typeof lastBuy.md === 'number' ? new Date(lastBuy.md).toLocaleDateString('zh-CN', { timeZone: 'Asia/Shanghai' }) : String(lastBuy.md).slice(0, 10);
          const todayLocal = new Date().toLocaleDateString('zh-CN', { timeZone: 'Asia/Shanghai' });
          pending = md === todayLocal;
        }"""
assert s.count(old) == 1
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('fixed slice on timestamp')
