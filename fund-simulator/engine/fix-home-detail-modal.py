# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue'
with io.open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. transactions map 增加 raw 原始日期（用于时间线排序）
old1 = """    transactions.value = txData.map((tx: any) => ({
      date: formatDate(tx.transaction_date),
      action: tx.transaction_type === 'BUY' ? '买入' : '卖出',"""
new1 = """    transactions.value = txData.map((tx: any) => ({
      date: formatDate(tx.transaction_date),
      raw: tx.transaction_date,
      action: tx.transaction_type === 'BUY' ? '买入' : '卖出',"""
assert old1 in c, 'anchor1 not found'
c = c.replace(old1, new1)

# 2. viewFundDetail 跳转 → 弹窗
old2 = """// 查看基金详情（跳转独立详情页，真实数据）
const viewFundDetail = (fund: any) => {
  const code = fund?.fund_code || fund?.code || fund?.fundCode
  if (code) router.push(`/funds/${code}`)
}"""
new2 = """// 基金详情弹窗（持仓明细/观察池 → 弹窗：操作记录时间线 + 基金信息，不再跳页）
const detailVisible = ref<boolean>(false)
const detailLoading = ref<boolean>(false)
const detailFund = ref<any>(null)
const detailTxs = ref<any[]>([])
const detailNavMap = ref<Record<string, number>>({})

const closeDetail = () => {
  detailVisible.value = false
}

// 该交易日增长率（按交易日期匹配净值历史）
const growthOf = (tx: any): number | null => {
  const day = String(tx.date).slice(0, 10)
  const g = detailNavMap.value[day]
  return g !== undefined && g !== null ? g : null
}

// 查看基金详情（弹窗展示，真实数据）
const viewFundDetail = async (fund: any) => {
  const code = fund?.fund_code || fund?.code || fund?.fundCode
  if (!code) return
  detailVisible.value = true
  detailLoading.value = true
  detailTxs.value = transactions.value
    .filter((tx: any) => tx.fund_code === code)
    .slice()
    .sort((a: any, b: any) => String(a.raw || '').localeCompare(String(b.raw || '')))
  detailFund.value = { code, name: fund?.fund_name || fund?.name || code }
  try {
    // 净值历史（含日增长率，按日期匹配）
    const navRes = await axios.get(`/api/funds/${code}/nav`, { params: { limit: 120 } })
    const navRows = Array.isArray(navRes.data) ? navRes.data : []
    const map: Record<string, number> = {}
    for (const n of navRows) {
      if (n.nav_date && n.daily_return != null) map[n.nav_date] = n.daily_return
    }
    detailNavMap.value = map
    // 基金基本信息
    const fundRes = await axios.get('/api/funds', { params: { limit: 100 } })
    const info = ((fundRes.data && fundRes.data.data) || []).find((f: any) => f.fund_code === code)
    if (info) {
      detailFund.value = {
        code: info.fund_code,
        name: info.fund_name,
        type: info.fund_type,
        manager: info.manager,
        inception_date: info.inception_date,
        benchmark: info.benchmark
      }
    }
  } catch (error) {
    console.error('加载基金详情失败:', error)
  } finally {
    detailLoading.value = false
  }
}"""
assert old2 in c, 'anchor2 not found'
c = c.replace(old2, new2)

# 3. 模板末尾加 Modal（在 </a-spin> 前）
old3 = """  </a-spin>
</template>"""
new3 = """    <!-- 基金详情弹窗：操作记录时间线（图标节点+增长率+悬浮明细） + 基金信息 -->
    <a-modal
      v-model:open="detailVisible"
      :footer="null"
      :width="760"
      destroy-on-close
      class="fund-detail-modal"
    >
      <template #title>
        <span v-if="detailFund">
          <span class="modal-title-name">{{ detailFund.name }}</span>
          <span class="modal-title-code">{{ detailFund.code }}</span>
        </span>
      </template>
      <a-spin :spinning="detailLoading">
        <div class="detail-modal-body">
          <div class="detail-section-title">操作记录</div>
          <div v-if="detailTxs.length === 0" class="empty-state">
            <div class="empty-icon">📝</div>
            <p>暂无该基金操作记录</p>
          </div>
          <a-timeline v-else class="detail-timeline">
            <a-timeline-item
              v-for="(tx, i) in detailTxs"
              :key="i"
              :color="tx.action === '买入' ? '#34d399' : '#f87171'"
            >
              <a-tooltip
                :title="`份额 ${tx.shares.toLocaleString()} 份 · 净值 ¥${tx.price.toFixed(4)} · 手续费 ¥${tx.fees.toFixed(2)}`"
                placement="right"
              >
                <div class="tx-node">
                  <div class="tx-growth" :class="growthOf(tx) != null && growthOf(tx) >= 0 ? 'profit' : 'loss'">
                    {{ growthOf(tx) != null ? (growthOf(tx) >= 0 ? '+' : '') + growthOf(tx).toFixed(2) + '%' : '—' }}
                  </div>
                  <div class="tx-main">
                    <span class="tx-icon" :class="tx.action === '买入' ? 'icon-buy' : 'icon-sell'">
                      {{ tx.action === '买入' ? '▲' : '▼' }}
                    </span>
                    <span class="tx-date">{{ tx.date }}</span>
                    <span class="tx-action" :class="tx.action === '买入' ? 'tag-buy' : 'tag-sell'">{{ tx.action }}</span>
                    <span class="tx-amount">¥{{ tx.amount.toFixed(2) }}</span>
                    <span class="tx-fee" v-if="tx.fees > 0">手续费 ¥{{ tx.fees.toFixed(2) }}</span>
                  </div>
                </div>
              </a-tooltip>
            </a-timeline-item>
          </a-timeline>

          <a-divider class="detail-divider" />

          <div class="detail-section-title">基金信息</div>
          <div class="detail-info-grid" v-if="detailFund">
            <div class="detail-info-item">
              <span class="label">基金代码</span>
              <span class="value">{{ detailFund.code }}</span>
            </div>
            <div class="detail-info-item">
              <span class="label">基金类型</span>
              <span class="value">{{ detailFund.type || '—' }}</span>
            </div>
            <div class="detail-info-item">
              <span class="label">基金经理</span>
              <span class="value">{{ detailFund.manager || '—' }}</span>
            </div>
            <div class="detail-info-item">
              <span class="label">成立日期</span>
              <span class="value">{{ detailFund.inception_date || '—' }}</span>
            </div>
            <div class="detail-info-item benchmark-item">
              <span class="label">业绩基准</span>
              <span class="value benchmark">{{ detailFund.benchmark || '—' }}</span>
            </div>
          </div>
        </div>
      </a-spin>
    </a-modal>
  </a-spin>
</template>"""
assert old3 in c, 'anchor3 not found'
c = c.replace(old3, new3)

# 4. 样式（</style> 前）
old4 = '</style>'
new4 = """/* 基金详情弹窗 */
.fund-detail-modal :deep(.ant-modal-content) {
  background: #1c2348;
  border: 1px solid #2c3466;
  border-radius: 16px;
}
.fund-detail-modal :deep(.ant-modal-header) {
  background: transparent;
  border-bottom: 1px solid #2c3466;
  padding-bottom: 14px;
}
.fund-detail-modal :deep(.ant-modal-title) {
  color: var(--text);
  font-weight: 600;
}
.modal-title-name { color: var(--text); }
.modal-title-code { color: var(--text-muted); font-size: 13px; margin-left: 8px; }
.detail-modal-body { padding: 4px 6px; }
.detail-section-title {
  color: var(--text);
  font-weight: 600;
  margin-bottom: 14px;
}
.detail-timeline {
  max-height: 320px;
  overflow-y: auto;
  padding: 4px 6px;
}
.detail-timeline :deep(.ant-timeline-item-tail) {
  border-left: 2px solid #2c3466;
}
.tx-node {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 2px 0 12px;
  cursor: default;
}
.tx-growth {
  font-size: 12px;
  font-weight: 600;
  line-height: 1.2;
}
.tx-growth.profit { color: #34d399; }
.tx-growth.loss { color: #f87171; }
.tx-main {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.tx-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 6px;
  font-size: 11px;
  color: #fff;
}
.tx-icon.icon-buy { background: rgba(52, 211, 153, 0.2); color: #34d399; }
.tx-icon.icon-sell { background: rgba(248, 113, 113, 0.2); color: #f87171; }
.tx-date { color: var(--text-muted); font-size: 13px; }
.tx-action { font-size: 12px; padding: 1px 8px; border-radius: 4px; font-weight: 500; }
.tx-action.tag-buy { background: rgba(52, 211, 153, 0.15); color: #34d399; }
.tx-action.tag-sell { background: rgba(248, 113, 113, 0.15); color: #f87171; }
.tx-amount { color: var(--text); font-weight: 600; font-size: 14px; }
.tx-fee { color: var(--text-muted); font-size: 12px; }
.detail-divider {
  border-color: #2c3466;
  margin: 4px 0 16px;
}
.detail-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 24px;
}
.detail-info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}
.detail-info-item .label { color: var(--text-muted); font-size: 13px; flex-shrink: 0; }
.detail-info-item .value { color: var(--text); font-weight: 500; text-align: right; }
.detail-info-item .benchmark { font-size: 12px; line-height: 1.5; }
.benchmark-item { grid-column: 1 / -1; }

</style>"""
assert old4 in c, 'anchor4 not found'
c = c.replace(old4, new4, 1)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c)
print('OK: Home.vue 详情改为弹窗')
