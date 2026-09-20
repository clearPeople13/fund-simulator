# -*- coding: utf-8 -*-
"""Funds.vue 基金排行：排序维度 tabs（近1周/1月/3月/6月/1年/今年来/成立来/规模）+ 动态主涨幅列"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Funds.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) script：rank 状态
old1 = """const total = ref(0)"""
new1 = """const total = ref(0)
// 基金排行维度（支付宝式：近1周/1月/3月/6月/1年/今年来/成立来/规模）
const rankTabs = [
  { key: 'r1w', label: '近1周' },
  { key: 'r1m', label: '近1月' },
  { key: 'r3m', label: '近3月' },
  { key: 'r6m', label: '近6月' },
  { key: 'r1y', label: '近1年' },
  { key: 'ytd', label: '今年来' },
  { key: 'since', label: '成立来' },
  { key: 'scale', label: '规模' }
]
const sortKey = ref('r6m')
const rankLabel = computed(() => (rankTabs.find(t => t.key === sortKey.value) || rankTabs[3]).label)"""
assert s.count(old1) == 1, 'block1 not found'
s = s.replace(old1, new1)

# 2) script：动态列 + loadFunds 用 sortKey
old2 = """// a-table 列配置
const tableColumns = [
  { title: '基金代码', dataIndex: 'fund_code', key: 'fund_code', width: 120 },
  { title: '基金名称', dataIndex: 'fund_name', key: 'fund_name' },
  { title: '基金类型', dataIndex: 'fund_type', key: 'fund_type', width: 130 },
  { title: '最新净值', key: 'latest_nav', width: 140 },
  { title: '近6月收益', key: 'recent_return', width: 120, align: 'right' },
  { title: '操作', key: 'actions', width: 200, fixed: 'right' }
]"""
new2 = """// a-table 列配置（主涨幅列随排行维度动态变化）
const tableColumns = computed(() => [
  { title: '基金代码', dataIndex: 'fund_code', key: 'fund_code', width: 110 },
  { title: '基金名称', dataIndex: 'fund_name', key: 'fund_name' },
  { title: '基金类型', dataIndex: 'fund_type', key: 'fund_type', width: 110 },
  { title: '最新净值', key: 'latest_nav', width: 130 },
  { title: rankLabel.value + (sortKey.value === 'scale' ? '（亿）' : '涨幅'), key: 'rank_value', width: 150, align: 'right' },
  { title: '近1年', key: 'r1y_col', width: 100, align: 'right' },
  { title: '操作', key: 'actions', width: 195, fixed: 'right' }
])"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

# 3) loadFunds sort
old3 = """        keyword: searchQuery.value || undefined,
        sort: 'r6m'"""
new3 = """        keyword: searchQuery.value || undefined,
        sort: sortKey.value"""
assert s.count(old3) == 1, 'block3 not found'
s = s.replace(old3, new3)

# 4) 切换维度
old4 = """// 页码变化 → 服务端重新加载"""
new4 = """// 切换排行维度 → 回到第 1 页重新加载
const handleRankChange = (key) => {
  sortKey.value = key
  currentPage.value = 1
  loadFunds()
}

// 当前维度值（scale 显示规模，其余为涨幅）
const rankValue = (record) => {
  const v = record[sortKey.value]
  return v != null ? v : null
}

// 页码变化 → 服务端重新加载"""
assert s.count(old4) == 1, 'block4 not found'
s = s.replace(old4, new4)

# 5) 模板：维度 tabs 放 filter-card 下方
old5 = """    <!-- 基金列表 -->
    <a-card class="fund-list-card" :bordered="false">"""
new5 = """    <!-- 基金排行维度 -->
    <div class="rank-bar">
      <span class="rank-title">🏆 基金排行</span>
      <div class="rank-tabs">
        <span
          v-for="t in rankTabs"
          :key="t.key"
          class="rank-tab"
          :class="{ active: sortKey === t.key }"
          @click="handleRankChange(t.key)"
        >{{ t.label }}</span>
      </div>
    </div>

    <!-- 基金列表 -->
    <a-card class="fund-list-card" :bordered="false">"""
assert s.count(old5) == 1, 'block5 not found'
s = s.replace(old5, new5)

# 6) 模板：recent_return 列替换为 rank_value + r1y
old6 = """          <template v-else-if="column.key === 'recent_return'">
            <span v-if="record.recent_return != null" :class="record.recent_return >= 0 ? 'profit' : 'loss'">
              {{ record.recent_return >= 0 ? '+' : '' }}{{ record.recent_return }}%
            </span>
            <span v-else>—</span>
          </template>"""
new6 = """          <template v-else-if="column.key === 'rank_value'">
            <template v-if="rankValue(record) != null">
              <template v-if="sortKey === 'scale'">
                <span>{{ Number(rankValue(record)).toLocaleString() }} 亿</span>
              </template>
              <template v-else>
                <div class="rank-cell">
                  <div class="rank-track">
                    <div class="rank-zero"></div>
                    <div
                      class="rank-fill"
                      :class="rankValue(record) >= 0 ? 'up' : 'down'"
                      :style="{ width: Math.min(48, Math.abs(rankValue(record))) + '%', left: rankValue(record) >= 0 ? '50%' : 'auto', right: rankValue(record) >= 0 ? 'auto' : (50 - Math.min(48, Math.abs(rankValue(record)))) + '%' }"
                    ></div>
                  </div>
                  <span :class="rankValue(record) >= 0 ? 'profit' : 'loss'">
                    {{ rankValue(record) >= 0 ? '+' : '' }}{{ rankValue(record) }}%
                  </span>
                </div>
              </template>
            </template>
            <span v-else class="muted">—</span>
          </template>
          <template v-else-if="column.key === 'r1y_col'">
            <span v-if="record.r1y != null" :class="record.r1y >= 0 ? 'profit' : 'loss'">
              {{ record.r1y >= 0 ? '+' : '' }}{{ record.r1y }}%
            </span>
            <span v-else class="muted">—</span>
          </template>"""
assert s.count(old6) == 1, 'block6 not found'
s = s.replace(old6, new6)

# 7) 样式
old7 = """.fund-list-card {
  margin-bottom: 20px;
}"""
new7 = """.fund-list-card {
  margin-bottom: 20px;
}

/* 排行维度 */
.rank-bar { display: flex; align-items: center; gap: 16px; margin: 0 0 14px; flex-wrap: wrap; }
.rank-title { font-size: 15px; font-weight: 700; color: var(--text); }
.rank-tabs { display: flex; gap: 6px; flex-wrap: wrap; }
.rank-tab {
  padding: 6px 14px; border-radius: 16px; cursor: pointer; font-size: 13px;
  color: var(--text-secondary); border: 1px solid var(--border); transition: all 0.2s; user-select: none;
}
.rank-tab:hover { color: var(--primary); border-color: var(--primary); }
.rank-tab.active { background: linear-gradient(135deg, rgba(99,102,241,0.25), rgba(139,92,246,0.15)); color: #a5b4fc; border-color: rgba(99,102,241,0.5); font-weight: 600; }

/* 涨幅条形 */
.rank-cell { display: flex; align-items: center; gap: 8px; justify-content: flex-end; }
.rank-track { position: relative; width: 96px; height: 6px; background: rgba(30,41,59,0.6); border-radius: 3px; }
.rank-zero { position: absolute; left: 50%; top: 0; bottom: 0; width: 1px; background: rgba(148,163,184,0.5); }
.rank-fill { position: absolute; top: 0; bottom: 0; border-radius: 3px; }
.rank-fill.up { background: linear-gradient(90deg, rgba(52,211,153,0.4), #34d399); }
.rank-fill.down { background: linear-gradient(90deg, #f87171, rgba(248,113,113,0.4)); }
.muted { color: var(--text-muted); }"""
assert s.count(old7) == 1, 'block7 not found'
s = s.replace(old7, new7)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Funds.vue rank patched')
