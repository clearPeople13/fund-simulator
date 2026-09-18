<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { FileTextOutlined, CalendarOutlined, ThunderboltOutlined, MoneyCollectOutlined, TagsOutlined } from '@ant-design/icons-vue'

interface Report {
  id: number
  user_id: string
  report_type: string
  period: string
  content: string
  created_at: string
}

const reports = ref<Report[]>([])
const current = ref<Report | null>(null)
const activeType = ref<'daily' | 'weekly' | 'monthly' | 'pressure' | 'fees'>('weekly')
const loading = ref(false)

// ---- 费用统计 ----
interface FeeRow {
  id: number
  transaction_date: string
  fund_code: string
  fund_name: string
  transaction_type: string
  amount: number
  shares: number
  price: number
  fees: number
  rate: number
}
interface FeeSummary { buy_fee: number; sell_fee: number; total_fee: number; trade_count: number }
interface FeeByFund { fund_code: string; fund_name: string; buy_fee: number; sell_fee: number; total_fee: number; buy_count: number; sell_count: number; buy_rate: number; sell_rate: number }

const feeSummary = ref<FeeSummary>({ buy_fee: 0, sell_fee: 0, total_fee: 0, trade_count: 0 })
const feeByFund = ref<FeeByFund[]>([])
const feeDetail = ref<FeeRow[]>([])
const feeLoading = ref(false)
const feeFilter = ref<'all' | 'BUY' | 'SELL'>('all')

const feeColumns = [
  { title: '交易时间', dataIndex: 'transaction_date', key: 'date', width: 170 },
  { title: '基金代码', dataIndex: 'fund_code', key: 'code', width: 100 },
  { title: '基金名称', dataIndex: 'fund_name', key: 'name' },
  { title: '操作', dataIndex: 'transaction_type', key: 'type', width: 90 },
  { title: '金额', dataIndex: 'amount', key: 'amount', width: 130, align: 'right' as const },
  { title: '手续费', dataIndex: 'fees', key: 'fees', width: 120, align: 'right' as const },
  { title: '费率', dataIndex: 'rate', key: 'rate', width: 110, align: 'right' as const }
]

const feeFundColumns = [
  { title: '基金代码', dataIndex: 'fund_code', key: 'code', width: 110 },
  { title: '基金名称', dataIndex: 'fund_name', key: 'name' },
  { title: '申购费', dataIndex: 'buy_fee', key: 'buy_fee', width: 120, align: 'right' as const },
  { title: '赎回费', dataIndex: 'sell_fee', key: 'sell_fee', width: 120, align: 'right' as const },
  { title: '费用合计', dataIndex: 'total_fee', key: 'total_fee', width: 120, align: 'right' as const },
  { title: '买入笔数', dataIndex: 'buy_count', key: 'buy_count', width: 100, align: 'right' as const },
  { title: '卖出笔数', dataIndex: 'sell_count', key: 'sell_count', width: 100, align: 'right' as const }
]

const loadFees = async () => {
  feeLoading.value = true
  try {
    const res = await axios.get('/api/ai/fees')
    feeSummary.value = res.data.summary || { buy_fee: 0, sell_fee: 0, total_fee: 0, trade_count: 0 }
    feeByFund.value = res.data.by_fund || []
    feeDetail.value = res.data.detail || []
  } catch (error) {
    console.error('加载费用统计失败:', error)
  } finally {
    feeLoading.value = false
  }
}

const filteredDetail = (): FeeRow[] => {
  if (feeFilter.value === 'all') return feeDetail.value
  return feeDetail.value.filter(d => d.transaction_type === feeFilter.value)
}

const fmtMoney = (v: number | null | undefined): string => {
  if (v == null) return '—'
  return '¥' + v.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
const fmtRate = (v: number | null | undefined): string => {
  if (v == null) return '—'
  return v.toFixed(4) + '%'
}

// ---- 报告 ----
const typeTabs = [
  { key: 'daily', label: '每日复盘', icon: CalendarOutlined },
  { key: 'weekly', label: '周报', icon: FileTextOutlined },
  { key: 'monthly', label: '月报', icon: FileTextOutlined },
  { key: 'pressure', label: '压力测试', icon: ThunderboltOutlined },
  { key: 'fees', label: '费用统计', icon: MoneyCollectOutlined }
]

// SQLite 存 UTC（无时区标记），按 UTC 解析转本地显示
const formatTime = (str: string | null | undefined): string => {
  if (!str) return '--'
  try {
    const d = new Date(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/.test(str) && !/[zZ]|[+-]\d{2}:\d{2}$/.test(str) ? str.replace(' ', 'T') + 'Z' : str.replace(' ', 'T'))
    if (isNaN(d.getTime())) return str
    return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
  } catch {
    return str
  }
}

const loadReports = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/reports', { params: { type: activeType.value } })
    reports.value = res.data.reports || []
    current.value = reports.value[0] || null
  } catch (error) {
    console.error('加载报告失败:', error)
  } finally {
    loading.value = false
  }
}

const showReport = (r: Report) => {
  current.value = r
}

const switchType = (key: string) => {
  activeType.value = key as typeof activeType.value
  if (key === 'fees') {
    loadFees()
  } else {
    loadReports()
  }
}

const renderContent = (content: string) => {
  if (!content) return ''
  return content
    .split('\n')
    .map(line => {
      let l = line
      if (l.startsWith('## ')) return '<h4 class="md-h4">' + l.slice(3) + '</h4>'
      if (l.startsWith('# ')) return '<h3 class="md-h3">' + l.slice(2) + '</h3>'
      if (l.startsWith('- ')) return '<div class="md-li">• ' + l.slice(2) + '</div>'
      if (l.trim() === '') return '<div class="md-space"></div>'
      return '<div class="md-p">' + l + '</div>'
    })
    .join('')
}

onMounted(loadReports)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title"><FileTextOutlined /> 报告中心</h1>
        <p class="page-desc">AI 基金经理自动生成：每日复盘、周报、月报、压力测试、费用统计</p>
      </div>
    </div>

    <a-card class="panel" :bordered="false">
      <div class="report-tabs">
        <div
          v-for="t in typeTabs"
          :key="t.key"
          class="report-tab"
          :class="{ active: activeType === t.key }"
          @click="switchType(t.key)"
        >
          <component :is="t.icon" class="tab-icon" />
          {{ t.label }}
        </div>
      </div>
    </a-card>

    <!-- 费用统计 -->
    <div v-if="activeType === 'fees'" class="fees-body">
      <a-spin :spinning="feeLoading">
        <div class="fees-summary">
          <div class="fee-stat">
            <div class="fee-stat-icon buy"><TagsOutlined /></div>
            <div class="fee-stat-body">
              <div class="fee-stat-label">累计申购费</div>
              <div class="fee-stat-value">{{ fmtMoney(feeSummary.buy_fee) }}</div>
            </div>
          </div>
          <div class="fee-stat">
            <div class="fee-stat-icon sell"><TagsOutlined /></div>
            <div class="fee-stat-body">
              <div class="fee-stat-label">累计赎回费</div>
              <div class="fee-stat-value">{{ fmtMoney(feeSummary.sell_fee) }}</div>
            </div>
          </div>
          <div class="fee-stat primary">
            <div class="fee-stat-icon total"><MoneyCollectOutlined /></div>
            <div class="fee-stat-body">
              <div class="fee-stat-label">费用合计</div>
              <div class="fee-stat-value">{{ fmtMoney(feeSummary.total_fee) }}</div>
            </div>
          </div>
          <div class="fee-stat">
            <div class="fee-stat-icon count"><FileTextOutlined /></div>
            <div class="fee-stat-body">
              <div class="fee-stat-label">涉及交易笔数</div>
              <div class="fee-stat-value">{{ feeSummary.trade_count }} 笔</div>
            </div>
          </div>
        </div>

        <a-card class="fee-card" :bordered="false">
          <template #title>按基金分组（费用组成）</template>
          <a-table
            :columns="feeFundColumns"
            :data-source="feeByFund"
            :pagination="false"
            row-key="fund_code"
            size="middle"
            :locale="{ emptyText: '暂无交易' }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'fund_name'">
                <span class="fund-name">{{ record.fund_name }}</span>
              </template>
              <template v-else-if="['buy_fee', 'sell_fee', 'total_fee'].includes(column.key)">
                <span :class="column.key === 'total_fee' ? 'fee-total' : ''">{{ fmtMoney(record[column.key]) }}</span>
              </template>
              <template v-else-if="['buy_count', 'sell_count'].includes(column.key)">
                <span class="muted">{{ record[column.key] }} 笔</span>
              </template>
            </template>
          </a-table>
          <div class="fee-note">
            费率说明：申购费/赎回费 = 手续费 ÷ 交易金额（内扣法，实际扣款即交易金额）。管理费/托管费已包含在每日净值中（按日计提后公布），不单独记账。
          </div>
        </a-card>

        <a-card class="fee-card" :bordered="false">
          <template #title>逐笔明细（可追溯）</template>
          <template #extra>
            <a-radio-group v-model:value="feeFilter" size="small" button-style="solid">
              <a-radio-button value="all">全部</a-radio-button>
              <a-radio-button value="BUY">买入</a-radio-button>
              <a-radio-button value="SELL">卖出</a-radio-button>
            </a-radio-group>
          </template>
          <a-table
            :columns="feeColumns"
            :data-source="filteredDetail()"
            :pagination="{ pageSize: 10, showSizeChanger: false }"
            row-key="id"
            size="middle"
            :locale="{ emptyText: '暂无费用记录' }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'date'">
                <span class="muted">{{ formatTime(record.transaction_date) }}</span>
              </template>
              <template v-else-if="column.key === 'type'">
                <a-tag :color="record.transaction_type === 'BUY' ? 'green' : 'red'">
                  {{ record.transaction_type === 'BUY' ? '买入' : '卖出' }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'amount'">
                <span>{{ fmtMoney(record.amount) }}</span>
              </template>
              <template v-else-if="column.key === 'fees'">
                <span class="fee-cell">{{ fmtMoney(record.fees) }}</span>
              </template>
              <template v-else-if="column.key === 'rate'">
                <span class="muted">{{ fmtRate(record.rate) }}</span>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-spin>
    </div>

    <!-- 报告 -->
    <div v-else class="report-body">
      <a-card class="report-list" :bordered="false" :loading="loading">
        <template #title>报告列表</template>
        <a-empty v-if="!reports.length" description="暂无报告（每日收盘后自动生成）" />
        <div
          v-for="r in reports"
          :key="r.id"
          class="report-item"
          :class="{ selected: current && current.id === r.id }"
          @click="showReport(r)"
        >
          <div class="report-item-title">{{ r.period }}</div>
          <div class="report-item-time">{{ formatTime(r.created_at) }}</div>
        </div>
      </a-card>

      <a-card class="report-view" :bordered="false">
        <template #title>
          <span v-if="current">报告 · {{ current.period }}</span>
          <span v-else>选择左侧报告查看</span>
        </template>
        <div v-if="current" class="md-body" v-html="renderContent(current.content)"></div>
        <a-empty v-else description="暂无报告内容" />
      </a-card>
    </div>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: 16px; max-width: 1080px; margin: 0 auto; width: 100%; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; }
.page-title { font-size: 22px; color: var(--text); display: flex; align-items: center; gap: 8px; }
.page-desc { color: var(--text-secondary); margin-top: 4px; }
.panel { background: var(--card); border-radius: var(--radius-md); }
.report-tabs { display: flex; gap: 12px; flex-wrap: wrap; }
.report-tab {
  display: flex; align-items: center; gap: 6px; padding: 10px 18px;
  border-radius: 10px; cursor: pointer; color: var(--text-secondary);
  border: 1px solid var(--border); transition: all 0.2s;
}
.report-tab:hover { color: var(--primary); border-color: var(--primary); }
.report-tab.active { background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.15)); color: var(--primary); border-color: var(--primary); }
.tab-icon { font-size: 15px; }
.report-body { display: grid; grid-template-columns: 280px 1fr; gap: 16px; align-items: start; }
.report-list { background: var(--card); border-radius: var(--radius-md); }
.report-item {
  padding: 12px 14px; border-radius: 10px; cursor: pointer; margin-bottom: 8px;
  border: 1px solid transparent; transition: all 0.2s;
}
.report-item:hover { border-color: var(--border); background: rgba(99,102,241,0.06); }
.report-item.selected { border-color: var(--primary); background: rgba(99,102,241,0.12); }
.report-item-title { font-size: 14px; color: var(--text); font-weight: 500; }
.report-item-time { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.report-view { background: var(--card); border-radius: var(--radius-md); min-height: 420px; }
.md-body { line-height: 1.8; }
.md-h3 { font-size: 17px; color: var(--text); margin: 14px 0 8px; }
.md-h4 { font-size: 15px; color: var(--primary); margin: 12px 0 6px; }
.md-li { color: var(--text); padding-left: 4px; margin: 3px 0; }
.md-p { color: var(--text); margin: 3px 0; }
.md-space { height: 4px; }

/* 费用统计 */
.fees-body { display: flex; flex-direction: column; gap: 16px; }
.fees-summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; }
.fee-stat {
  display: flex; align-items: center; gap: 12px; padding: 18px;
  background: var(--card); border-radius: var(--radius-md); border: 1px solid var(--border);
}
.fee-stat-icon {
  width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px;
}
.fee-stat-icon.buy { background: rgba(52,211,153,0.15); color: #34d399; }
.fee-stat-icon.sell { background: rgba(248,113,113,0.15); color: #f87171; }
.fee-stat-icon.total { background: linear-gradient(135deg, rgba(99,102,241,0.25), rgba(139,92,246,0.2)); color: #818cf8; }
.fee-stat-icon.count { background: rgba(251,191,36,0.15); color: #fbbf24; }
.fee-stat-label { font-size: 12px; color: var(--text-muted); }
.fee-stat-value { font-size: 20px; font-weight: 700; color: var(--text); margin-top: 2px; }
.fee-card { background: var(--card); border-radius: var(--radius-md); }
.fund-name { color: var(--text); font-weight: 500; }
.fee-total { color: var(--primary); font-weight: 600; }
.fee-cell { color: #fbbf24; font-weight: 600; }
.muted { color: var(--text-muted); font-size: 12px; }
.fee-note { margin-top: 12px; padding: 10px 14px; background: rgba(99,102,241,0.06); border-radius: 10px; font-size: 12px; color: var(--text-muted); line-height: 1.7; }
</style>
