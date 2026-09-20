# -*- coding: utf-8 -*-
import io

path = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue'
with io.open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. 交易记录映射加 fees
old1 = """      price: tx.price,
      reason: tx.reason
    }))"""
new1 = """      price: tx.price,
      fees: tx.fees || 0,
      reason: tx.reason
    }))"""
if old1 not in c:
    print('锚点1未找到')
    raise SystemExit(1)
c = c.replace(old1, new1)

# 2. 交易记录表头加手续费列
old2 = """                <th>基金名称</th>
                <th>金额</th>"""
new2 = """                <th>基金名称</th>
                <th>金额</th>
                <th>手续费</th>"""
if old2 not in c:
    print('锚点2未找到')
    raise SystemExit(1)
c = c.replace(old2, new2)

# 3. 交易记录行加手续费单元格（金额 td 后）
old3 = """                <td class="number">¥{{ tx.amount.toFixed(2) }}</td>
                <td class="number">{{ tx.shares.toLocaleString() }}</td>"""
new3 = """                <td class="number">¥{{ tx.amount.toFixed(2) }}</td>
                <td class="number" :class="tx.fees > 0 ? 'fee' : ''">{{ tx.fees > 0 ? '¥' + tx.fees.toFixed(2) : '—' }}</td>
                <td class="number">{{ tx.shares.toLocaleString() }}</td>"""
if old3 not in c:
    print('锚点3未找到')
    raise SystemExit(1)
c = c.replace(old3, new3)

with io.open(path, 'w', encoding='utf-8', newline='') as f:
    f.write(c)
print('交易记录手续费列已加')
