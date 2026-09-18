<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { WarningOutlined, DatabaseOutlined, BellOutlined } from '@ant-design/icons-vue'

interface RiskEvent {
  id: number
  event_type: string
  fund_code: string
  detail: string
  action: string
  created_at: string
}
interface DataQuality {
  id: number
  fund_code: string
  nav_date: string
  issue_type: string
  detail: string
  created_at: string
}

const events = ref<RiskEvent[]>([])
const dataQuality = ref<DataQuality[]>([])
const loading = ref(false)

const eventTagColor = (type: string) => {
  if (type.includes('STOP_LOSS') || type.includes('BLOCKED')) return 'error'
  if (type.includes('REDUCE') || type.includes('DRAWDOWN')) return 'warning'
  if (type.includes('DIVIDEND') || type.includes('SWITCH')) return 'success'
  return 'processing'
}

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

const loadAlerts = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/alerts')
    events.value = res.data.events || []
    dataQuality.value = res.data.data_quality || []
  } catch (error) {
    console.error('加载预警失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(loadAlerts)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title"><BellOutlined /> 预警中心</h1>
        <p class="page-desc">聚合持仓预警、观察池异动、风控事件与数据质量告警</p>
      </div>
      <a-button type="primary" ghost @click="loadAlerts">刷新</a-button>
    </div>

    <div class="alert-stats">
      <a-card class="stat-card" :bordered="false">
        <div class="stat-num">{{ events.filter(e => e.event_type.includes('STOP_LOSS') || e.event_type.includes('BLOCKED')).length }}</div>
        <div class="stat-label">高风险事件</div>
      </a-card>
      <a-card class="stat-card" :bordered="false">
        <div class="stat-num">{{ events.filter(e => e.event_type.includes('REDUCE')).length }}</div>
        <div class="stat-label">减仓/预警</div>
      </a-card>
      <a-card class="stat-card" :bordered="false">
        <div class="stat-num">{{ dataQuality.length }}</div>
        <div class="stat-label">数据异常</div>
      </a-card>
    </div>

    <a-card class="panel" :bordered="false" :loading="loading">
      <template #title><WarningOutlined /> 风控事件</template>
      <a-table
        :data-source="events"
        :columns="[
          { title: '时间', dataIndex: 'created_at', width: 170 },
          { title: '事件类型', dataIndex: 'event_type', width: 170 },
          { title: '基金', dataIndex: 'fund_code', width: 110 },
          { title: '动作', dataIndex: 'action', width: 100 },
          { title: '详情', dataIndex: 'detail' }
        ]"
        :pagination="{ pageSize: 10 }"
        size="middle"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'created_at'">{{ formatTime(record.created_at) }}</template>
          <template v-else-if="column.dataIndex === 'event_type'">
            <a-tag :color="eventTagColor(record.event_type)">{{ record.event_type }}</a-tag>
          </template>
          <template v-else-if="column.dataIndex === 'action'">
            <a-tag>{{ record.action || '-' }}</a-tag>
          </template>
          <template v-else-if="column.dataIndex === 'detail'">
            <span class="detail-text">{{ record.detail }}</span>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-card class="panel" :bordered="false" :loading="loading">
      <template #title><DatabaseOutlined /> 数据质量告警</template>
      <a-empty v-if="!dataQuality.length" description="暂无数据异常，净值数据质量正常" />
      <a-table
        v-else
        :data-source="dataQuality"
        :columns="[
          { title: '时间', dataIndex: 'created_at', width: 170 },
          { title: '基金', dataIndex: 'fund_code', width: 110 },
          { title: '净值日期', dataIndex: 'nav_date', width: 120 },
          { title: '类型', dataIndex: 'issue_type', width: 110 },
          { title: '详情', dataIndex: 'detail' }
        ]"
        :pagination="{ pageSize: 10 }"
        size="middle"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'created_at'">{{ formatTime(record.created_at) }}</template>
          <template v-else-if="column.dataIndex === 'issue_type'">
            <a-tag color="warning">{{ record.issue_type }}</a-tag>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: 16px; max-width: 1080px; margin: 0 auto; width: 100%; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; }
.page-title { font-size: 22px; color: var(--text); display: flex; align-items: center; gap: 8px; }
.page-desc { color: var(--text-secondary); margin-top: 4px; }
.alert-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.stat-card { background: var(--card); border-radius: var(--radius-md); }
.stat-num { font-size: 28px; font-weight: 700; background: linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.stat-label { color: var(--text-secondary); font-size: 13px; margin-top: 4px; }
.panel { background: var(--card); border-radius: var(--radius-md); }
.detail-text { color: var(--text); }
</style>
