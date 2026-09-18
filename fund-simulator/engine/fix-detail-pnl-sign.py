# -*- coding: utf-8 -*-
"""修正收益/汇总显示：Math.abs 吞掉负号，改为保留符号（负号自带，正数加 +）"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) 收益列：负号保留
old1 = """                  <td :class="row.pnl != null && row.pnl >= 0 ? 'profit' : 'loss'">
                    <template v-if="row.pnl != null">
                      {{ row.pnl >= 0 ? '+' : '' }}¥{{ Math.abs(row.pnl).toFixed(2) }}
                      <span class="pnl-tag" :class="row.pnl_tag === '实' ? 'realized' : 'floating'">{{ row.pnl_tag === '实' ? '已实现' : '浮动' }}</span>
                    </template>
                    <template v-else><span class="nav-date">—</span></template>
                  </td>
                  <td :class="row.pnl_rate != null && row.pnl_rate >= 0 ? 'profit' : 'loss'">
                    <template v-if="row.pnl_rate != null">{{ row.pnl_rate >= 0 ? '+' : '' }}{{ row.pnl_rate.toFixed(2) }}%</template>
                    <template v-else><span class="nav-date">—</span></template>
                  </td>"""
new1 = """                  <td :class="row.pnl != null && row.pnl >= 0 ? 'profit' : 'loss'">
                    <template v-if="row.pnl != null">
                      <template v-if="row.pnl >= 0">+</template>¥{{ row.pnl.toFixed(2) }}
                      <span class="pnl-tag" :class="row.pnl_tag === '实' ? 'realized' : 'floating'">{{ row.pnl_tag === '实' ? '已实现' : '浮动' }}</span>
                    </template>
                    <template v-else><span class="nav-date">—</span></template>
                  </td>
                  <td :class="row.pnl_rate != null && row.pnl_rate >= 0 ? 'profit' : 'loss'">
                    <template v-if="row.pnl_rate != null"><template v-if="row.pnl_rate >= 0">+</template>{{ row.pnl_rate.toFixed(2) }}%</template>
                    <template v-else><span class="nav-date">—</span></template>
                  </td>"""
assert s.count(old1) == 1, 'block1 not found'
s = s.replace(old1, new1)

# 2) 汇总条：符号保留
old2 = """              <span :class="detailPnlSummary.realized >= 0 ? 'profit' : 'loss'">已实现 {{ detailPnlSummary.realized >= 0 ? '+' : '' }}¥{{ Math.abs(detailPnlSummary.realized).toFixed(2) }}</span>
              <span class="sum-sep">·</span>
              <span :class="detailPnlSummary.floating >= 0 ? 'profit' : 'loss'">持有浮动 {{ detailPnlSummary.floating >= 0 ? '+' : '' }}¥{{ Math.abs(detailPnlSummary.floating).toFixed(2) }}</span>
              <span class="sum-sep">·</span>
              <span :class="detailPnlSummary.total >= 0 ? 'profit' : 'loss'" class="sum-total">该基金合计 {{ detailPnlSummary.total >= 0 ? '+' : '' }}¥{{ Math.abs(detailPnlSummary.total).toFixed(2) }}</span>"""
new2 = """              <span :class="detailPnlSummary.realized >= 0 ? 'profit' : 'loss'">已实现 <template v-if="detailPnlSummary.realized >= 0">+</template>¥{{ detailPnlSummary.realized.toFixed(2) }}</span>
              <span class="sum-sep">·</span>
              <span :class="detailPnlSummary.floating >= 0 ? 'profit' : 'loss'">持有浮动 <template v-if="detailPnlSummary.floating >= 0">+</template>¥{{ detailPnlSummary.floating.toFixed(2) }}</span>
              <span class="sum-sep">·</span>
              <span :class="detailPnlSummary.total >= 0 ? 'profit' : 'loss'" class="sum-total">该基金合计 <template v-if="detailPnlSummary.total >= 0">+</template>¥{{ detailPnlSummary.total.toFixed(2) }}</span>"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Home.vue patched')
