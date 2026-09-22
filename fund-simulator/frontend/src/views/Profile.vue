<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { message, Modal } from 'ant-design-vue'
import { UserOutlined, SafetyCertificateOutlined, FundOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons-vue'

interface User {
  id: string
  name: string
  avatar: string
  style: string
  description: string
}

const users = ref<User[]>([])
const paramsMap = ref<Record<string, any>>({})
const loading = ref(false)
const addModalVisible = ref(false)
const adding = ref(false)
const form = ref({
  name: '',
  style: '稳健型',
  initial_capital: 100000,
  description: ''
})

const loadAll = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/roles')
    users.value = res.data.roles
    for (const u of res.data.roles) {
      try {
        const p = await axios.get(`/api/risk/params/${u.id}`)
        paramsMap.value[u.id] = p.data.params || {}
      } catch(e) {
        paramsMap.value[u.id] = u
      }
    }
  } catch (error) {
    console.error('加载角色失败:', error)
  } finally {
    loading.value = false
  }
}

const paramRows = (userId: string) => {
  const p = paramsMap.value[userId] || {}
  const rows = [
    { label: '风险偏好', value: p.risk_tolerance === 'high' ? '高（激进）' : p.risk_tolerance === 'medium' ? '中（稳健）' : p.risk_tolerance, key: 'risk_tolerance' },
    { label: '目标年化收益', value: p.target_return != null ? (p.target_return * 100).toFixed(0) + '%' : '-', key: 'target_return' },
    { label: '单基金止损线', value: p.stop_loss != null ? '-' + (p.stop_loss * 100).toFixed(0) + '%' : '-', key: 'stop_loss' },
    { label: '单基金止盈线', value: p.take_profit != null ? '+' + (p.take_profit * 100).toFixed(0) + '%' : '-', key: 'take_profit' },
    { label: '总仓位上限', value: p.max_position != null ? (p.max_position * 100).toFixed(0) + '%' : '-', key: 'max_position' },
    { label: '单基金仓位上限', value: p.max_single_fund != null ? (p.max_single_fund * 100).toFixed(0) + '%' : '-', key: 'max_single_fund' },
    { label: '最少持仓基金数', value: p.min_hold_funds != null ? p.min_hold_funds + ' 只' : '-', key: 'min_hold_funds' },
    { label: '组合回撤熔断线', value: p.max_drawdown != null ? '-' + (p.max_drawdown * 100).toFixed(0) + '%' : '-', key: 'max_drawdown' },
    { label: '单基回撤评估阈值', value: p.exit_drawdown != null ? p.exit_drawdown + '%' : '-', key: 'exit_drawdown' },
    { label: '退场风格', value: p.exit_style === 'timely' ? '及时（触发即减/清）' : p.exit_style === 'patient' ? '容忍（恶化确认后减）' : p.exit_style || '-', key: 'exit_style' },
    { label: '入场信号门槛', value: p.entry_signal_threshold === 'strong' ? '仅强信号' : p.entry_signal_threshold === 'medium' ? '中信号及以上' : p.entry_signal_threshold || '-', key: 'entry_signal_threshold' },
    { label: '建仓比例', value: p.buy_ratio != null ? (p.buy_ratio * 100).toFixed(0) + '% 资金' : '-', key: 'buy_ratio' },
    { label: '加仓比例', value: p.add_ratio != null ? (p.add_ratio * 100).toFixed(0) + '% 资金' : '-', key: 'add_ratio' },
    { label: '再平衡频率', value: p.rebalance_frequency === 'weekly' ? '每周' : p.rebalance_frequency === 'monthly' ? '每月' : p.rebalance_frequency || '-', key: 'rebalance_frequency' },
    { label: '选基偏好', value: p.watchlist_style || '-', key: 'watchlist_style' }
  ]
  return rows
}

const isDefaultRole = (id: string) => id === 'default' || id === 'aggressive'

const handleAdd = async () => {
  if (!form.value.name) {
    message.warning('请输入角色名称')
    return
  }
  adding.value = true
  try {
    await axios.post('/api/roles', form.value)
    message.success(`角色「${form.value.name}」已创建，AI 将自动开始按性格操作`)
    addModalVisible.value = false
    form.value = { name: '', style: '稳健型', initial_capital: 100000, description: '' }
    await loadAll()
  } catch (e: any) {
    message.error(e.response?.data?.error || '创建失败')
  } finally {
    adding.value = false
  }
}

const handleDelete = (u: User) => {
  Modal.confirm({
    title: `删除角色「${u.name}」？`,
    content: '删除后该角色不再自动运行，持仓和交易记录保留。',
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await axios.delete(`/api/roles/${u.id}`)
        message.success('角色已删除')
        await loadAll()
      } catch (e: any) {
        message.error(e.response?.data?.error || '删除失败')
      }
    }
  })
}

onMounted(loadAll)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title"><UserOutlined /> AI 基金经理画像</h1>
        <p class="page-desc">每个角色是一位独立的 AI 基金经理，性格参数驱动全部交易决策。可添加新角色，AI 会自动按性格跑流程。</p>
      </div>
      <a-button type="primary" @click="addModalVisible = true">
        <template #icon><PlusOutlined /></template>
        添加 AI 角色
      </a-button>
    </div>

    <div class="profile-grid">
      <a-card
        v-for="u in users"
        :key="u.id"
        class="profile-card"
        :bordered="false"
        :loading="loading"
      >
        <template #title>
          <div class="profile-head">
            <span class="avatar">{{ u.avatar }}</span>
            <div>
              <div class="profile-name">{{ u.name }}</div>
              <a-tag :color="u.style === '激进型' ? 'volcano' : 'processing'">{{ u.style }}</a-tag>
            </div>
            <a-button
              v-if="!isDefaultRole(u.id)"
              type="text"
              danger
              size="small"
              class="delete-btn"
              @click="handleDelete(u)"
            >
              <template #icon><DeleteOutlined /></template>
            </a-button>
          </div>
        </template>
        <p class="profile-desc">{{ u.description }}</p>

        <div class="param-section">
          <div class="param-title"><SafetyCertificateOutlined /> 风控参数</div>
          <div class="param-list">
            <div v-for="row in paramRows(u.id).filter(r => ['risk_tolerance','target_return','stop_loss','take_profit','max_position','max_single_fund','min_hold_funds','max_drawdown','exit_drawdown'].includes(r.key))" :key="row.key" class="param-row">
              <span class="param-label">{{ row.label }}</span>
              <span class="param-value">{{ row.value }}</span>
            </div>
          </div>
        </div>

        <div class="param-section">
          <div class="param-title"><FundOutlined /> 决策参数</div>
          <div class="param-list">
            <div v-for="row in paramRows(u.id).filter(r => ['exit_style','entry_signal_threshold','buy_ratio','add_ratio','rebalance_frequency','watchlist_style'].includes(r.key))" :key="row.key" class="param-row">
              <span class="param-label">{{ row.label }}</span>
              <span class="param-value">{{ row.value }}</span>
            </div>
          </div>
        </div>
      </a-card>
    </div>

    <!-- 添加角色弹窗 -->
    <a-modal v-model:open="addModalVisible" title="添加 AI 角色" :confirm-loading="adding" @ok="handleAdd">
      <a-form layout="vertical" style="margin-top: 16px">
        <a-form-item label="角色名称" required>
          <a-input v-model:value="form.name" placeholder="如：稳健型小白、趋势猎手..." />
        </a-form-item>
        <a-form-item label="投资风格">
          <a-radio-group v-model:value="form.style">
            <a-radio value="稳健型">🛡️ 稳健型（低风险、严格止损、分散持仓）</a-radio>
            <a-radio value="激进型">🚀 激进型（高风险、追求收益、集中持仓）</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="初始资金">
          <a-input-number v-model:value="form.initial_capital" :min="10000" :step="10000" style="width: 100%" />
        </a-form-item>
        <a-form-item label="角色描述">
          <a-input v-model:value="form.description" placeholder="一句话描述这个 AI 的投资理念..." />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: 16px; max-width: 1080px; margin: 0 auto; width: 100%; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; }
.page-title { font-size: 22px; color: var(--text); display: flex; align-items: center; gap: 8px; }
.page-desc { color: var(--text-secondary); margin-top: 4px; max-width: 600px; }
.profile-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.profile-card { background: var(--card); border-radius: var(--radius-md); }
.profile-head { display: flex; align-items: center; gap: 10px; }
.avatar { font-size: 30px; }
.profile-name { font-size: 16px; color: var(--text); font-weight: 600; margin-bottom: 2px; }
.delete-btn { margin-left: auto; }
.profile-desc { color: var(--text-secondary); font-size: 13px; margin: 8px 0 16px; }
.param-section { margin-top: 12px; }
.param-title { font-size: 14px; font-weight: 600; color: var(--primary); margin-bottom: 8px; display: flex; align-items: center; gap: 6px; }
.param-list { display: flex; flex-direction: column; gap: 6px; }
.param-row { display: flex; justify-content: space-between; padding: 8px 12px; background: rgba(99, 102, 241, 0.05); border-radius: 8px; }
.param-label { color: var(--text-secondary); font-size: 13px; }
.param-value { color: var(--text); font-size: 13px; font-weight: 600; }
</style>
