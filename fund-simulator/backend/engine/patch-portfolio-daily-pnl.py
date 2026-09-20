# -*- coding: utf-8 -*-
"""Portfolio.vue 补：①每日收益明细表（账户级跨基金按日贡献+快照对照）②持仓/明细导出 CSV"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Portfolio.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) ref
old1 = """const holdings = ref([])"""
new1 = """const holdings = ref([])
const dailyPnl = ref<any[]>([]) // 每日收益明细
const fundNames = ref<any>({})"""
assert s.count(old1) == 1, 'block1 not found'
s = s.replace(old1, new1)

# 2) loadData 加载每日收益明细
old2 = """    loading.value = false
    setTimeout(() => initAllocationChart(), 100)"""
new2 = """    // 每日收益明细（账户级跨基金按日贡献 + 账户快照对照）
    try {
      const dpRes = await axios.get('/api/ai/daily-pnl')
      if (dpRes.data && dpRes.data.list) {
        dailyPnl.value = dpRes.data.list
        fundNames.value = dpRes.data.fund_names || {}
      }
    } catch (e) {
      console.error('加载每日收益明细失败:', e)
    }
    loading.value = false
    setTimeout(() => initAllocationChart(), 100)"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

# 3) 导出 CSV 函数
old3 = """onMounted(() => {
  loadData()
})"""
new3 = """// 导出持仓 + 每日收益明细 CSV（纯前端 Blob 下载）
const exportCSV = () => {
  const esc = (v: any) => { const t = String(v ?? '').replace(/"/g, '""'); return `"${t}"` }
  const lines: string[] = []
  lines.push('持仓明细导出（' + new Date().toLocaleString() + '）')
  lines.push(['代码', '基金名称', '类型', '份额', '成本价', '现价', '市值', '盈亏', '收益率'].join(','))
  holdings.value.forEach(r => lines.push([r.fund_code, r.fund_name, r.fund_type, r.shares, r.cost_price, r.current_price, r.market_value, r.profit_loss, r.profit_loss_rate + '%'].map(esc).join(',')))
  lines.push('')
  lines.push('每日收益明细（日期,当日盈亏,账户快照对照' + Object.keys(fundNames.value).map(c => ',' + c + ' ' + fundNames.value[c]).join('') + '）')
  dailyPnl.value.forEach(r => {
    const fundCols = Object.keys(fundNames.value).map(c => r.funds && r.funds[c] != null ? r.funds[c] : '')
    lines.push([r.date, r.pnl, r.account_pnl != null ? r.account_pnl : '待更新', ...fundCols].join(','))
  })
  const blob = new Blob(['\\ufeff' + lines.join('\\r\\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '组合明细_' + new Date().toISOString().slice(0, 10) + '.csv'
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  loadData()
})"""
assert s.count(old3) == 1, 'block3 not found'
s = s.replace(old3, new3)

# 4) 模板：持仓卡头加导出按钮
old4 = """          <template #title>
            <div class="card-header">
              <span class="block-title-no-margin">持仓明细</span>
              <a-tag>{{ holdings.length }} 只</a-tag>
            </div>
          </template>"""
new4 = """          <template #title>
            <div class="card-header">
              <span class="block-title-no-margin">持仓明细</span>
              <span>
                <a-tag>{{ holdings.length }} 只</a-tag>
                <a-button size="small" style="margin-left:8px" @click="exportCSV">导出 CSV</a-button>
              </span>
            </div>
          </template>"""
assert s.count(old4) == 1, 'block4 not found'
s = s.replace(old4, new4)

# 5) 模板：资产配置卡后加每日收益明细卡
old5 = """      <!-- 资产配置 -->
      <a-col :xs="24" :md="8">
        <a-card :bordered="false" class="allocation-card" title="资产配置">
          <div id="allocationChart" class="chart-container"></div>
        </a-card>
      </a-col>
    </a-row>
  </div>"""
new5 = """      <!-- 资产配置 -->
      <a-col :xs="24" :md="8">
        <a-card :bordered="false" class="allocation-card" title="资产配置">
          <div id="allocationChart" class="chart-container"></div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 每日收益明细（账户级跨基金按日贡献） -->
    <a-card :bordered="false" style="margin-top:20px">
      <template #title>
        <div class="card-header">
          <span class="block-title-no-margin">📅 每日收益明细</span>
          <a-tag>当日盈亏 = 收盘份额 × 净值变动（买入当日 T+1 无收益）</a-tag>
        </div>
      </template>
      <a-table
        :columns="dailyColumns"
        :data-source="dailyPnl"
        :pagination="false"
        row-key="date"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'pnl'">
            <span :class="record.pnl >= 0 ? 'profit' : 'loss'">
              <template v-if="record.pnl > 0">+</template>{{ record.pnl.toFixed(2) }}
            </span>
          </template>
          <template v-else-if="column.key === 'account_pnl'">
            <span v-if="record.account_pnl == null" style="color:#64748b">待更新</span>
            <span v-else :class="record.account_pnl >= 0 ? 'profit' : 'loss'">
              <template v-if="record.account_pnl > 0">+</template>{{ Number(record.account_pnl).toFixed(2) }}
            </span>
          </template>
          <template v-else-if="column.key.startsWith('fund_')">
            <template v-if="record.funds && record.funds[column.key.slice(5)] != null">
              <span :class="record.funds[column.key.slice(5)] >= 0 ? 'profit' : 'loss'">
                <template v-if="record.funds[column.key.slice(5)] > 0">+</template>{{ record.funds[column.key.slice(5)].toFixed(2) }}
              </span>
            </template>
            <template v-else><span style="color:#475569">—</span></template>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>"""
assert s.count(old5) == 1, 'block5 not found'
s = s.replace(old5, new5)

# 6) 动态列 computed（在 script 中）
old6 = """// 初始化资产配置图（真实持仓数据）"""
new6 = """// 每日收益明细动态列（每只持仓基金一列）
const dailyColumns = computed(() => {
  const base = [
    { title: '日期', dataIndex: 'date', key: 'date', width: 110 },
    { title: '当日盈亏', key: 'pnl', width: 110, align: 'right' as const },
    { title: '账户快照对照', key: 'account_pnl', width: 130, align: 'right' as const }
  ]
  const fundCols = Object.keys(fundNames.value).map(c => ({
    title: `${c} ${fundNames.value[c]}`,
    key: 'fund_' + c,
    align: 'right' as const
  }))
  return [...base, ...fundCols]
})

// 初始化资产配置图（真实持仓数据）"""
assert s.count(old6) == 1, 'block6 not found'
s = s.replace(old6, new6)

# 7) import computed
old7 = """import { ref, onMounted } from 'vue'"""
new7 = """import { ref, computed, onMounted } from 'vue'"""
assert s.count(old7) == 1, 'block7 not found'
s = s.replace(old7, new7)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Portfolio.vue patched')
