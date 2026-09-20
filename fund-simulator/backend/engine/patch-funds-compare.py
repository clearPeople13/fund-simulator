# -*- coding: utf-8 -*-
"""Funds.vue 基金对比：列表勾选最多3只 → 弹窗并排对比（代码/净值/各区间涨幅/规模/成立日期）"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Funds.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) 对比状态
old1 = """const sortKey = ref('r6m')"""
new1 = """const sortKey = ref('r6m')
// 基金对比（最多 3 只）
const compareCodes = ref([])
const compareVisible = ref(false)
const compareRows = computed(() => {
  const selected = compareCodes.value.map(code => filteredFunds.value.find(f => f.fund_code === code)).filter(Boolean)
  const metrics = [
    { key: 'fund_name', label: '基金名称' },
    { key: 'fund_type', label: '基金类型' },
    { key: 'latest_nav', label: '最新净值', fmt: v => v != null ? '¥' + v : '—' },
    { key: 'day_return', label: '日涨跌', pct: true },
    { key: 'r1w', label: '近1周', pct: true },
    { key: 'r1m', label: '近1月', pct: true },
    { key: 'r3m', label: '近3月', pct: true },
    { key: 'r6m', label: '近6月', pct: true },
    { key: 'r1y', label: '近1年', pct: true },
    { key: 'ytd', label: '今年来', pct: true },
    { key: 'since', label: '成立来', pct: true },
    { key: 'scale', label: '规模(亿)', fmt: v => v != null ? Number(v).toLocaleString() : '—' },
    { key: 'inception_date', label: '成立日期' }
  ]
  return metrics.map(m => ({
    label: m.label,
    cells: selected.map(f => {
      const v = f[m.key === 'r6m' ? 'recent_return' : m.key]
      if (m.fmt) return { text: m.fmt(v), pct: false }
      if (m.pct) return { text: v != null ? (v >= 0 ? '+' : '') + v + '%' : '—', pct: true, value: v }
      return { text: v != null ? v : '—', pct: false }
    })
  }))
})
const toggleCompare = (code) => {
  const idx = compareCodes.value.indexOf(code)
  if (idx >= 0) {
    compareCodes.value.splice(idx, 1)
  } else if (compareCodes.value.length >= 3) {
    return false
  } else {
    compareCodes.value.push(code)
  }
  return true
}"""
assert s.count(old1) == 1, 'block1 not found'
s = s.replace(old1, new1)

# 2) 列配置加对比勾选列
old2 = """  { title: '操作', key: 'actions', width: 195, fixed: 'right' }
])"""
new2 = """  { title: '对比', key: 'compare', width: 90, align: 'center' },
  { title: '操作', key: 'actions', width: 195, fixed: 'right' }
])"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

# 3) 模板：排行条右侧加对比按钮
old3 = """    <!-- 基金列表 -->
    <a-card class="fund-list-card" :bordered="false">"""
new3 = """    <!-- 对比操作 -->
    <div v-if="compareCodes.length" class="compare-bar">
      <span>已选 <b>{{ compareCodes.length }}</b> 只（最多 3 只）</span>
      <a-button type="primary" size="small" @click="compareVisible = true">开始对比</a-button>
      <a-button size="small" @click="compareCodes = []">清空</a-button>
    </div>

    <!-- 基金列表 -->
    <a-card class="fund-list-card" :bordered="false">"""
assert s.count(old3) == 1, 'block3 not found'
s = s.replace(old3, new3)

# 4) 表格 bodyCell 加 compare 列
old4 = """          <template v-else-if="column.key === 'actions'">"""
new4 = """          <template v-else-if="column.key === 'compare'">
            <a-checkbox
              :checked="compareCodes.includes(record.fund_code)"
              :disabled="!compareCodes.includes(record.fund_code) && compareCodes.length >= 3"
              @change="toggleCompare(record.fund_code)"
            />
          </template>
          <template v-else-if="column.key === 'actions'">"""
assert s.count(old4) == 1, 'block4 not found'
s = s.replace(old4, new4)

# 5) 对比弹窗（列表卡后）
old5 = """    </a-card>
  </div>
</template>"""
new5 = """    </a-card>

    <!-- 基金对比弹窗 -->
    <a-modal v-model:open="compareVisible" title="📊 基金对比" :footer="null" width="860" :destroy-on-close="true">
      <div v-if="compareRows.length" class="compare-table-wrap">
        <table class="compare-table">
          <thead>
            <tr>
              <th class="metric-col">指标</th>
              <th v-for="(r, ri) in compareRows[0].cells" :key="ri">{{ compareCodes[ri] || '—' }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in compareRows" :key="idx">
              <td class="metric-col">{{ row.label }}</td>
              <td v-for="(c, ci) in row.cells" :key="ci">
                <span v-if="c.pct" :class="c.value >= 0 ? 'profit' : 'loss'">{{ c.text }}</span>
                <span v-else-if="row.label === '基金名称'" class="fund-name" @click="viewFundDetail(compareCodes[ci])">{{ c.text }}</span>
                <span v-else>{{ c.text }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <a-empty v-else description="请先在列表勾选基金" />
    </a-modal>
  </div>
</template>"""
assert s.count(old5) == 1, 'block5 not found'
s = s.replace(old5, new5)

# 6) 样式
old6 = """.muted { color: var(--text-muted); }"""
new6 = """.muted { color: var(--text-muted); }
.compare-bar { display: flex; align-items: center; gap: 10px; margin: 0 0 14px; padding: 10px 16px; background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.25); border-radius: 10px; font-size: 13px; color: var(--text); }
.compare-table-wrap { overflow-x: auto; }
.compare-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.compare-table th, .compare-table td { padding: 9px 12px; border-bottom: 1px solid rgba(148,163,184,0.15); text-align: center; color: var(--text); }
.compare-table th { background: rgba(99,102,241,0.1); color: #a5b4fc; font-weight: 600; }
.compare-table .metric-col { text-align: left; color: var(--text-secondary); white-space: nowrap; }"""
assert s.count(old6) == 1, 'block6 not found'
s = s.replace(old6, new6)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Funds.vue compare patched')
