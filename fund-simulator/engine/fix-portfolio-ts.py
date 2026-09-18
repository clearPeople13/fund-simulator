# -*- coding: utf-8 -*-
"""Portfolio.vue 无 lang=ts，去掉 TS 语法（ref<any[]>、as const、类型注解）"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Portfolio.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

repls = [
    ("const dailyPnl = ref<any[]>([]) // 每日收益明细", "const dailyPnl = ref([]) // 每日收益明细"),
    ("const fundNames = ref<any>({})", "const fundNames = ref({})"),
    ("const esc = (v: any) => { const t = String(v ?? '').replace(/\"/g, '\"\"'); return `\"${t}\"` }", "const esc = (v) => { const t = String(v ?? '').replace(/\"/g, '\"\"'); return `\"${t}\"` }"),
    ("{ title: '当日盈亏', key: 'pnl', width: 110, align: 'right' as const },", "{ title: '当日盈亏', key: 'pnl', width: 110, align: 'right' },"),
    ("{ title: '账户快照对照', key: 'account_pnl', width: 130, align: 'right' as const }", "{ title: '账户快照对照', key: 'account_pnl', width: 130, align: 'right' }"),
    ("    key: 'fund_' + c,\n    align: 'right' as const", "    key: 'fund_' + c,\n    align: 'right'"),
]
for old, new in repls:
    assert s.count(old) == 1, 'not found: ' + old[:40]
    s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Portfolio.vue TS cleaned')
