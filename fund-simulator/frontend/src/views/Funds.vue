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

// a-table 列配置
const tableColumns = [
  { title: '基金代码', dataIndex: 'fund_code', key: 'fund_code', width: 120 },
  { title: '基金名称', dataIndex: 'fund_name', key: 'fund_name' },
  { title: '基金类型', dataIndex: 'fund_type', key: 'fund_type', width: 130 },
  { title: '最新净值', key: 'latest_nav', width: 140 },
  { title: '近6月收益', key: 'recent_return', width: 120, align: 'right' },
  { title: '操作', key: 'actions', width: 200, fixed: 'right' }
]

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
        sort: 'r6m'
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
          <template v-else-if="column.key === 'recent_return'">
            <span v-if="record.recent_return != null" :class="record.recent_return >= 0 ? 'profit' : 'loss'">
              {{ record.recent_return >= 0 ? '+' : '' }}{{ record.recent_return }}%
            </span>
            <span v-else>—</span>
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

.fund-name {
  color: #a5b4fc;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.2s;
}

.fund-name:hover {
  color: #818cf8;
}

.profit {
  color: #34d399;
  font-weight: 600;
}

.loss {
  color: #f87171;
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
