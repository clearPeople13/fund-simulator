# -*- coding: utf-8 -*-
import io
p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue'
c = io.open(p, encoding='utf-8').read()
# 在 .t1-tag 定义前插入 .est-time（就近锚点：.profit/.loss 定义后）
old = """.profit { color: #10b981; font-weight: 600; }
.loss { color: #ef4444; font-weight: 600; }
"""
new = """.profit { color: #10b981; font-weight: 600; }
.loss { color: #ef4444; font-weight: 600; }

.est-time {
  margin-left: 4px;
  cursor: help;
}
"""
assert c.count(old) == 1, 'anchor'
c = c.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK est-time css')
