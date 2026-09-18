<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const activeTab = ref('buy')
const selectedFund = ref(route.query.fund_code || '')
const buyAmount = ref('')
const sellShares = ref('')
const capital = ref(100000)

// 持仓列表
const holdings = ref([
  { fund_code: '110011', fund_name: '易方达中小盘混合', shares: 2000, current_price: 5.89 },
  { fund_code: '161725', fund_name: '招商中证白酒指数', shares: 1500, current_price: 1.72 },
  { fund_code: '005827', fund_name: '易方达蓝筹精选混合', shares: 1800, current_price: 2.38 },
  { fund_code: '003834', fund_name: '华夏能源革新股票', shares: 2500, current_price: 4.25 },
  { fund_code: '005267', fund_name: '嘉实核心优势股票', shares: 1200, current_price: 1.98 }
])

// 交易历史
const transactions = ref([
  { date: '2024-01-15', fund_code: '110011', fund_name: '易方达中小盘混合', type: 'BUY', amount: 10000, shares: 2000, price: 5.00 },
  { date: '2024-01-20', fund_code: '161725', fund_name: '招商中证白酒指数', type: 'BUY', amount: 5000, shares: 1500, price: 3.33 },
  { date: '2024-02-05', fund_code: '003834', fund_name: '华夏能源革新股票', type: 'BUY', amount: 8000, shares: 2500, price: 3.20 },
  { date: '2024-02-15', fund_code: '005827', fund_name: '易方达蓝筹精选混合', type: 'BUY', amount: 6000, shares: 1800, price: 3.33 },
  { date: '2024-03-01', fund_code: '005267', fund_name: '嘉实核心优势股票', type: 'BUY', amount: 3000, shares: 1200, price: 2.50 }
])

// 计算可买份额
const estimatedShares = computed(() => {
  if (!selectedFund.value || !buyAmount.value) return 0
  const amount = parseFloat(buyAmount.value)
  if (isNaN(amount) || amount <= 0) return 0
  // 假设净值为5.0
  return (amount / 5.0).toFixed(2)
})

// 买入
const handleBuy = () => {
  if (!selectedFund.value || !buyAmount.value) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  const amount = parseFloat(buyAmount.value)
  if (amount > capital.value) {
    ElMessage.error('可用资金不足')
    return
  }
  
  ElMessageBox.confirm(
    `确认买入基金 ${selectedFund.value}，金额 ¥${amount.toLocaleString()}？`,
    '确认交易',
    { confirmButtonText: '确认', cancelButtonText: '取消', type: 'info' }
  ).then(() => {
    capital.value -= amount
    transactions.value.unshift({
      date: new Date().toISOString().split('T')[0],
      fund_code: selectedFund.value,
      fund_name: '基金名称',
      type: 'BUY',
      amount: amount,
      shares: parseFloat(estimatedShares.value),
      price: 5.0
    })
    ElMessage.success('买入成功！')
    buyAmount.value = ''
  }).catch(() => {})
}

// 卖出
const handleSell = () => {
  ElMessage.info('卖出功能开发中...')
}

onMounted(() => {
  if (route.query.action === 'buy') {
    activeTab.value = 'buy'
  }
})
</script>

<template>
  <div class="trading-container">
    <div class="page-header">
      <h1>模拟交易</h1>
      <p>使用虚拟资金进行基金买卖操作</p>
    </div>

    <!-- 可用资金 -->
    <el-card class="capital-card" shadow="hover">
      <div class="capital-info">
        <span class="label">可用资金：</span>
        <span class="value">¥{{ capital.toLocaleString() }}</span>
      </div>
    </el-card>

    <el-row :gutter="20">
      <!-- 交易表单 -->
      <el-col :xs="24" :md="12">
        <el-card shadow="hover">
          <el-tabs v-model="activeTab">
            <el-tab-pane label="买入" name="buy">
              <el-form label-width="80px">
                <el-form-item label="基金代码">
                  <el-input v-model="selectedFund" placeholder="请输入基金代码" />
                </el-form-item>
                <el-form-item label="买入金额">
                  <el-input v-model="buyAmount" placeholder="请输入买入金额" type="number">
                    <template #prefix>¥</template>
                  </el-input>
                </el-form-item>
                <el-form-item label="预估份额">
                  <span class="estimated">{{ estimatedShares }} 份</span>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="handleBuy" style="width: 100%">
                    <el-icon><ShoppingCart /></el-icon> 确认买入
                  </el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>
            <el-tab-pane label="卖出" name="sell">
              <el-form label-width="80px">
                <el-form-item label="基金代码">
                  <el-select v-model="selectedFund" placeholder="选择持仓基金" style="width: 100%">
                    <el-option
                      v-for="item in holdings"
                      :key="item.fund_code"
                      :label="`${item.fund_code} - ${item.fund_name}`"
                      :value="item.fund_code"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="卖出份额">
                  <el-input v-model="sellShares" placeholder="请输入卖出份额" type="number">
                    <template #suffix>份</template>
                  </el-input>
                </el-form-item>
                <el-form-item>
                  <el-button type="danger" @click="handleSell" style="width: 100%">
                    <el-icon><SoldOut /></el-icon> 确认卖出
                  </el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>

      <!-- 当前持仓 -->
      <el-col :xs="24" :md="12">
        <el-card shadow="hover">
          <template #header><span>当前持仓</span></template>
          <el-table :data="holdings" size="small" stripe>
            <el-table-column prop="fund_code" label="代码" width="90" />
            <el-table-column prop="fund_name" label="名称" min-width="140" show-overflow-tooltip />
            <el-table-column label="份额" width="80">
              <template #default="{ row }">{{ row.shares.toLocaleString() }}</template>
            </el-table-column>
            <el-table-column label="现价" width="70">
              <template #default="{ row }">¥{{ row.current_price.toFixed(2) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 交易历史 -->
    <el-card shadow="hover" class="history-card">
      <template #header><span>交易历史</span></template>
      <el-table :data="transactions" stripe>
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="fund_code" label="基金代码" width="100" />
        <el-table-column prop="fund_name" label="基金名称" min-width="180" />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.type === 'BUY' ? 'success' : 'danger'" size="small">
              {{ row.type === 'BUY' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="120">
          <template #default="{ row }">¥{{ row.amount.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="份额" width="100">
          <template #default="{ row }">{{ row.shares.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="净值" width="80">
          <template #default="{ row }">¥{{ row.price.toFixed(2) }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.trading-container { padding: 20px 0; }
.page-header { text-align: center; margin-bottom: 30px; }
.page-header h1 { font-size: 2.5rem; color: #303133; margin-bottom: 10px; }
.page-header p { font-size: 1.1rem; color: #606266; }
.capital-card { margin-bottom: 20px; }
.capital-info { display: flex; align-items: center; justify-content: center; gap: 10px; }
.capital-info .label { font-size: 16px; color: #606266; }
.capital-info .value { font-size: 28px; font-weight: 700; color: #409eff; }
.estimated { font-size: 16px; color: #67c23a; font-weight: 600; }
.history-card { margin-top: 20px; }
</style>