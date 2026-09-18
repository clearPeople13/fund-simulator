# -*- coding: utf-8 -*-
"""修正收益明细当日盈亏符号：负号保留"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """                  <td :class="row.pnl >= 0 ? 'profit' : 'loss'">
                    <template v-if="row.pnl !== 0 || row.shares === 0">{{ row.pnl >= 0 ? '+' : '' }}¥{{ Math.abs(row.pnl).toFixed(2) }}</template>
                    <template v-else><span class="nav-date">T+1</span></template>
                  </td>"""
new = """                  <td :class="row.pnl >= 0 ? 'profit' : 'loss'">
                    <template v-if="row.pnl !== 0 || row.shares === 0"><template v-if="row.pnl > 0">+</template>¥{{ row.pnl.toFixed(2) }}</template>
                    <template v-else><span class="nav-date">T+1</span></template>
                  </td>"""
assert s.count(old) == 1, 'block not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Home.vue patched')
