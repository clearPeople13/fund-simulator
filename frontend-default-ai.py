import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\App.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 默认 analysisMode='ai'（不是 'rule'）
old = "const analysisMode = ref<'rule' | 'ai'>('rule')"
new = "const analysisMode = ref<'rule' | 'ai'>('ai')  // 默认走 AI"
assert s.count(old) == 1
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('frontend default AI mode')
