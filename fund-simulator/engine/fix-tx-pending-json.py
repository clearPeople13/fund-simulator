# -*- coding: utf-8 -*-
"""/api/ai/transactions 返回结构改为 { list, pending }（数组附加属性会被 JSON 序列化丢弃）"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """      pending.push({ ...p, fund_name: fund ? fund.fund_name : p.fund_code });
    }
    res.json(Object.assign(enriched, { pending }));"""
new = """      pending.push({ ...p, fund_name: fund ? fund.fund_name : p.fund_code });
    }
    res.json({ list: enriched, pending });"""
assert s.count(old) == 1, 'backend block not found'
s = s.replace(old, new)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('server.js patched')

# 前端兼容
p2 = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p2, 'r', encoding='utf-8') as f:
    s2 = f.read()
old2 = """    const txRes = await axios.get('/api/ai/transactions')
    const txData = Array.isArray(txRes.data) ? txRes.data : []"""
new2 = """    const txRes = await axios.get('/api/ai/transactions')
    const txData = Array.isArray(txRes.data) ? txRes.data : (txRes.data?.list || [])"""
assert s2.count(old2) == 1, 'frontend block not found'
s2 = s2.replace(old2, new2)
with io.open(p2, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s2)
print('Home.vue patched')
