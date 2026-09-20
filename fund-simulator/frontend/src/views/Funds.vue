<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { SearchOutlined } from '@ant-design/icons-vue'
import axios from 'axios'

const router = useRouter()
const loading = ref(false)
const funds = ref([])
const searchQuery = ref('')
const selectedType = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
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
}
const rankLabel = computed(() => (rankTabs.find(t => t.key === sortKey.value) || rankTabs[3]).label)

// 基金类型选项（全市场基金库：股票型/混合型/指数型/QDII）
const fundTypes = [
  { value: '', label: '全部类型' },
  { value: '股票型', label: '股票型' },
  { value: '混合型', label: '混合型' },
  { value: '指数型', label: '指数型' },
  { value: 'QDII', label: 'QDII' }
]

// 类型标签颜色映射
const getTypeColor = (type) => {
  const map = {
    '股票型': 'red',
    '混合型': 'orange',
    '指数型': 'blue',
    'QDII': 'purple'
  }
  return map[type] || 'default'
}

// 基金列表数据（服务端分页/搜索/类型过滤）
const filteredFunds = computed(() => funds.value)

// a-table 列配置（主涨幅列随排行维度动态变化）
const tableColumns = computed(() => [
  { title: '基金代码', dataIndex: 'fund_code', key: 'fund_code', width: 110 },
  { title: '基金名称', dataIndex: 'fund_name', key: 'fund_name', width: 240 },
  { title: '基金类型', dataIndex: 'fund_type', key: 'fund_type', width: 110 },
  { title: '最新净值', key: 'latest_nav', width: 130 },
  { title: rankLabel.value + (sortKey.value === 'scale' ? '（亿）' : '涨幅'), key: 'rank_value', width: 150, align: 'right' },
  { title: '近1年', key: 'r1y_col', width: 100, align: 'right' },
  { title: '对比', key: 'compare', width: 90, align: 'center' },
  { title: '操作', key: 'actions', width: 195, fixed: 'right' }
])

// 加载基金列表（全市场基金库，服务端分页）
const loadFunds = async () => {
  try {
    loading.value = true
    const response = await axios.get('/api/funds', {
      params: {
        page: currentPage.value,
        limit: pageSize.value,
        type: selectedType.value || undefined,
        keyword: searchQuery.value || undefined,
        sort: sortKey.value
      }
    })
    funds.value = (response.data && response.data.data) || []
    total.value = (response.data && response.data.pagination && response.data.pagination.total) || 0
  } catch (error) {
    console.error('加载基金列表失败:', error)
    funds.value = []
  } finally {
    loading.value = false
  }
}

// 查看基金详情
const viewFundDetail = (code) => {
  router.push(`/funds/${code}`)
}

// 切换排行维度 → 回到第 1 页重新加载
const handleRankChange = (key) => {
  sortKey.value = key
  currentPage.value = 1
  loadFunds()
}

// 当前维度值（scale 显示规模，其余为涨幅；后端 r6m 返回为 recent_return 别名）
const rankValue = (record) => {
  const key = sortKey.value === 'r6m' ? 'recent_return' : sortKey.value
  const v = record[key]
  return v != null ? v : null
}

// 页码变化 → 服务端重新加载
const handleCurrentChange = (page) => {
  currentPage.value = page
  loadFunds()
}

// 搜索/类型变化 → 回到第 1 页重新加载
const handleFilterChange = () => {
  currentPage.value = 1
  loadFunds()
}

// ===== 自选观察池 =====
const currentUserId = ref('default')
const watchedCodes = ref(new Set())

// 加载当前用户与已自选基金
const loadWatchState = async () => {
  try {
    const userRes = await axios.get('/api/users/current')
    currentUserId.value = userRes.data.id
    const watchRes = await axios.get(`/api/users/${currentUserId.value}/watchlist`)
    watchedCodes.value = new Set((watchRes.data || []).map(w => w.fund_code))
  } catch (error) {
    console.error('加载自选状态失败:', error)
  }
}

const isWatched = (code) => watchedCodes.value.has(code)

// 添加/取消自选
const toggleWatch = async (code) => {
  try {
    const watching = isWatched(code)
    if (watching) {
      await axios.delete(`/api/users/${currentUserId.value}/watchlist/${code}`)
    } else {
      await axios.post(`/api/users/${currentUserId.value}/watchlist`, { fund_code: code })
    }
    // 更新本地状态
    const newSet = new Set(watchedCodes.value)
    watching ? newSet.delete(code) : newSet.add(code)
    watchedCodes.value = newSet
  } catch (error) {
    console.error('自选操作失败:', error)
  }
}

onMounted(() => {
  loadFunds()
  loadWatchState()
})
</script>

<template>
  <div class="funds-container">
    <!-- Hero 头图 -->
    <div class="page-hero">
      <div class="hero-inner">
        <div>
          <div class="hero-tag">基金库</div>
          <h1>基金列表</h1>
          <p class="hero-desc">浏览和筛选基金，找到适合您的投资标的</p>
        </div>
        <div class="hero-stat">
          <span class="hero-stat-num">{{ total }}</span>
          <span class="hero-stat-label">只基金 · 全市场基金库</span>
        </div>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <a-card class="filter-card" :bordered="false">
      <a-row :gutter="20" :align="'middle'">
        <a-col :xs="24" :md="8">
          <a-input
            v-model:value="searchQuery"
            placeholder="搜索基金代码或名称"
            allow-clear
            @change="handleFilterChange"
          >
            <template #prefix>
              <SearchOutlined style="color: var(--text-muted)" />
            </template>
          </a-input>
        </a-col>
        <a-col :xs="24" :md="8">
          <a-select v-model:value="selectedType" placeholder="选择基金类型" style="width: 100%" @change="handleFilterChange">
            <a-select-option
              v-for="item in fundTypes"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </a-select>
        </a-col>
        <a-col :xs="24" :md="8">
          <div class="filter-info">
            <a-tag>共 {{ total }} 只 · AI 选基范围即全市场</a-tag>
          </div>
        </a-col>
      </a-row>
    </a-card>

    <!-- 基金排行维度 -->
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

    <!-- 对比操作 -->
    <div v-if="compareCodes.length" class="compare-bar">
      <span>已选 <b>{{ compareCodes.length }}</b> 只（最多 3 只）</span>
      <a-button type="primary" size="small" @click="compareVisible = true">开始对比</a-button>
      <a-button size="small" @click="compareCodes = []">清空</a-button>
    </div>

    <!-- 基金列表 -->
    <a-card class="fund-list-card" :bordered="false">
      <a-table
        :columns="tableColumns"
        :data-source="filteredFunds"
        :loading="loading"
        :pagination="false"
        row-key="fund_code"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'fund_name'">
            <span class="fund-name" @click="viewFundDetail(record.fund_code)">{{ record.fund_name }}</span>
          </template>
          <template v-else-if="column.key === 'fund_type'">
            <a-tag :color="getTypeColor(record.fund_type)">{{ record.fund_type }}</a-tag>
          </template>
          <template v-else-if="column.key === 'latest_nav'">
            <span>{{ record.latest_nav != null ? '¥' + record.latest_nav : '—' }}</span>
            <div class="nav-date" v-if="record.latest_nav_date">{{ record.latest_nav_date }}</div>
          </template>
          <template v-else-if="column.key === 'rank_value'">
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
          </template>
          <template v-else-if="column.key === 'compare'">
            <a-checkbox
              :checked="compareCodes.includes(record.fund_code)"
              :disabled="!compareCodes.includes(record.fund_code) && compareCodes.length >= 3"
              @change="toggleCompare(record.fund_code)"
            />
          </template>
          <template v-else-if="column.key === 'actions'">
            <div style="display: flex; gap: 8px">
              <a-button
                :type="isWatched(record.fund_code) ? 'warning' : 'primary'"
                size="small"
                ghost
                @click="toggleWatch(record.fund_code)"
              >
                {{ isWatched(record.fund_code) ? '★ 已观察' : '☆ 观察' }}
              </a-button>
              <a-button type="primary" size="small" @click="viewFundDetail(record.fund_code)">
                详情
              </a-button>
            </div>
          </template>
        </template>
      </a-table>

      <!-- 分页 -->
      <div class="pagination">
        <a-pagination
          v-model:current="currentPage"
          :page-size="pageSize"
          :total="total"
          :show-total="(t) => `共 ${t} 只`"
          @change="handleCurrentChange"
        />
      </div>
    </a-card>

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
</template>

<style scoped>
.funds-container {
  padding: 0 0 32px;
  max-width: 1400px;
  margin: 0 auto;
}

/* Hero 右侧统计 */
.hero-stat {
  text-align: right;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 16px;
}

.hero-stat-num {
  display: block;
  font-size: 30px;
  font-weight: 700;
  color: #fff;
  line-height: 1.2;
}

.hero-stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.filter-card {
  margin-bottom: 20px;
  border-radius: 14px;
}

.filter-info {
  text-align: right;
}

.fund-list-card {
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
.rank-fill.up { background: linear-gradient(90deg, rgba(248,113,113,0.4), #f87171); }
.rank-fill.down { background: linear-gradient(90deg, #34d399, rgba(52,211,153,0.4)); }
.muted { color: var(--text-muted); }
.compare-bar { display: flex; align-items: center; gap: 10px; margin: 0 0 14px; padding: 10px 16px; background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.25); border-radius: 10px; font-size: 13px; color: var(--text); }
.compare-table-wrap { overflow-x: auto; }
.compare-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.compare-table th, .compare-table td { padding: 9px 12px; border-bottom: 1px solid rgba(148,163,184,0.15); text-align: center; color: var(--text); }
.compare-table th { background: rgba(99,102,241,0.1); color: #a5b4fc; font-weight: 600; }
.compare-table .metric-col { text-align: left; color: var(--text-secondary); white-space: nowrap; }

.fund-name {
  color: #a5b4fc;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.2s;
  white-space: normal;
  word-break: normal;
  line-height: 1.4;
  display: inline-block;
}

.fund-name:hover {
  color: #818cf8;
}

.profit {
  color: #f87171;
  font-weight: 600;
}

.loss {
  color: #34d399;
  font-weight: 600;
}

.nav-date {
  font-size: 12px;
  color: var(--text-muted);
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
