# -*- coding: utf-8 -*-
"""Home.vue 补缺：① 待确认订单展示 ② 资产配置环形图 ③ 收益构成（已实现+浮动）拆分条"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) ref 声明
old1 = """const transactions = ref<any[]>([])
const watchList = ref<any[]>([])"""
new1 = """const transactions = ref<any[]>([])
const pendingTxs = ref<any[]>([]) // 待确认订单（T+1）
const watchList = ref<any[]>([])"""
assert s.count(old1) == 1, 'block1 not found'
s = s.replace(old1, new1)

# 2) 收益构成 computed（累计收益 = 已实现 + 浮动）
old2 = """const totalPnlRate = computed(() => {"""
new2 = """// 收益构成：已实现盈亏 + 持仓浮动盈亏（累计收益 = 两者之和）
const pnlBreakdown = computed(() => {
  const p = portfolio.value
  if (!p) return { realized: 0, floating: 0, total: 0 }
  const realized = p.realized_pnl || 0
  const hs = holdings.value
  const floating = hs.reduce((sum, h) => sum + ((h.market_value || 0) - (h.total_cost || 0)), 0)
  const total = Math.round((realized + floating) * 100) / 100
  return { realized: Math.round(realized * 100) / 100, floating: Math.round(floating * 100) / 100, total }
})

const totalPnlRate = computed(() => {"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

# 3) 加载待确认订单
old3 = """    transactions.value = txData.map((tx: any) => ({"""
new3 = """    pendingTxs.value = (txRes.data && txRes.data.pending) || []
    transactions.value = txData.map((tx: any) => ({"""
assert s.count(old3) == 1, 'block3 not found'
s = s.replace(old3, new3)

# 4) initCharts 增加资产配置环形图
old4 = """const initCharts = () => {"""
new4 = """// 资产配置环形图：各持仓市值 + 现金占比
const initAllocChart = () => {
  const el = document.getElementById('allocChart')
  if (!el || !(window as any).echarts) return
  const chart = (window as any).echarts.getInstanceByDom(el) || (window as any).echarts.init(el)
  const hs = holdings.value
  const cash = portfolio.value?.current_capital || 0
  const items = hs.map(h => ({ name: h.fund_name || h.fund_code, value: Math.round((h.market_value || 0) * 100) / 100 }))
  items.push({ name: '现金', value: Math.round(cash * 100) / 100 })
  chart.setOption({
    color: ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#f43f5e', '#64748b'],
    tooltip: { trigger: 'item', formatter: (p: any) => `${p.name}: ¥${Number(p.value).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}（${p.percent}%）` },
    legend: { bottom: 0, textStyle: { color: '#94a3b8', fontSize: 12 }, itemWidth: 12, itemHeight: 12 },
    series: [{
      type: 'pie', radius: ['46%', '72%'], center: ['50%', '44%'],
      itemStyle: { borderRadius: 6, borderColor: '#131a35', borderWidth: 2 },
      label: { color: '#cbd5e1', fontSize: 11, formatter: '{b}\\n{d}%' },
      data: items
    }],
    grid: { containLabel: true }
  })
}

const initCharts = () => {"""
assert s.count(old4) == 1, 'block4 not found'
s = s.replace(old4, new4)

# 5) initCharts 内调用
old5 = """  initAssetChart()
  initPnlChart()"""
new5 = """  initAssetChart()
  initPnlChart()
  initAllocChart()"""
assert s.count(old5) == 1, 'block5 not found'
s = s.replace(old5, new5)

# 6) 模板：图表区加资产配置卡
old6 = """      <div class="chart-card">
        <div class="chart-header">
          <h3>📊 每日盈亏</h3>
        </div>
        <div id="pnlChart" class="chart-container"></div>
      </div>
    </div>"""
new6 = """      <div class="chart-card">
        <div class="chart-header">
          <h3>📊 每日盈亏</h3>
        </div>
        <div id="pnlChart" class="chart-container"></div>
      </div>
      <div class="chart-card">
        <div class="chart-header">
          <h3>🥧 资产配置</h3>
          <span class="nav-date">持仓市值 + 现金占比</span>
        </div>
        <div id="allocChart" class="chart-container"></div>
      </div>
    </div>"""
assert s.count(old6) == 1, 'block6 not found'
s = s.replace(old6, new6)

# 7) 模板：卡片区下方加收益构成条
old7 = """      <div class="overview-card warning">
        <div class="card-icon">📦</div>
        <div class="card-content">
          <div class="card-label">持仓数量</div>
          <div class="card-value">{{ holdings.length }} 只</div>
        </div>
      </div>
    </div>"""
new7 = """      <div class="overview-card warning">
        <div class="card-icon">📦</div>
        <div class="card-content">
          <div class="card-label">持仓数量</div>
          <div class="card-value">{{ holdings.length }} 只</div>
        </div>
      </div>
    </div>

    <!-- 收益构成：累计收益 = 已实现 + 浮动 -->
    <div class="pnl-breakdown">
      <div class="bd-item">
        <span class="bd-label">已实现盈亏</span>
        <span :class="pnlBreakdown.realized >= 0 ? 'profit' : 'loss'">
          <template v-if="pnlBreakdown.realized >= 0">+</template>¥{{ pnlBreakdown.realized.toFixed(2) }}
        </span>
      </div>
      <div class="bd-item">
        <span class="bd-label">持仓浮动盈亏</span>
        <span :class="pnlBreakdown.floating >= 0 ? 'profit' : 'loss'">
          <template v-if="pnlBreakdown.floating >= 0">+</template>¥{{ pnlBreakdown.floating.toFixed(2) }}
        </span>
      </div>
      <div class="bd-item bd-total">
        <span class="bd-label">累计收益（已实现 + 浮动）</span>
        <span :class="pnlBreakdown.total >= 0 ? 'profit' : 'loss'">
          <template v-if="pnlBreakdown.total >= 0">+</template>¥{{ pnlBreakdown.total.toFixed(2) }}
        </span>
      </div>
    </div>"""
assert s.count(old7) == 1, 'block7 not found'
s = s.replace(old7, new7)

# 8) 模板：交易记录上方加待确认订单
old8 = """    <!-- 交易记录 -->
    <div class="card">
      <div class="card-header">
        <h3>📝 交易记录</h3>
        <span class="badge info">{{ transactions.length }} 笔</span>
      </div>"""
new8 = """    <!-- 待确认订单（T+1） -->
    <div v-if="pendingTxs.length" class="card">
      <div class="card-header">
        <h3>⏳ 待确认订单</h3>
        <span class="badge warning">{{ pendingTxs.length }} 笔 · T+1 确认（20:00 按官方净值落账）</span>
      </div>
      <div class="card-body">
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>下单日</th>
                <th>操作</th>
                <th>基金代码</th>
                <th>基金名称</th>
                <th>金额</th>
                <th>份额</th>
                <th>参考净值</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in pendingTxs" :key="p.id">
                <td>{{ formatDate(p.order_date) }}</td>
                <td>
                  <span :class="p.order_type === 'BUY' ? 'tag-buy' : 'tag-sell'">
                    {{ p.order_type === 'BUY' ? '买入' : '卖出' }}
                  </span>
                </td>
                <td class="code">{{ p.fund_code }}</td>
                <td class="name">{{ p.fund_name }}</td>
                <td class="number">{{ p.order_type === 'BUY' ? '¥' + p.amount.toFixed(2) : '—' }}</td>
                <td class="number">{{ p.shares ? p.shares.toLocaleString() : '—' }}</td>
                <td class="number">¥{{ p.price.toFixed(4) }}</td>
                <td><span class="tag-pending">待确认</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 交易记录 -->
    <div class="card">
      <div class="card-header">
        <h3>📝 交易记录</h3>
        <span class="badge info">{{ transactions.length }} 笔</span>
      </div>"""
assert s.count(old8) == 1, 'block8 not found'
s = s.replace(old8, new8)

# 9) 样式
old9 = """.pnl-breakdown"""
if old9 not in s:
    anchor = """<style scoped>"""
    css = """<style scoped>
/* 收益构成条 */
.pnl-breakdown { display: flex; flex-wrap: wrap; gap: 12px; margin: 14px 0 4px; }
.bd-item { display: flex; align-items: center; gap: 10px; padding: 10px 18px; background: var(--card-bg, #1c2348); border: 1px solid rgba(99,102,241,0.15); border-radius: 10px; font-size: 13px; }
.bd-item .bd-label { color: #94a3b8; }
.bd-item.bd-total { background: linear-gradient(135deg, rgba(99,102,241,0.18), rgba(139,92,246,0.12)); border-color: rgba(99,102,241,0.35); }
.profit { color: #34d399; }
.loss { color: #f87171; }
.nav-date { color: #64748b; font-size: 12px; }
.tag-pending { display: inline-block; padding: 2px 10px; border-radius: 10px; font-size: 12px; background: rgba(245,158,11,0.15); color: #f59e0b; }
"""
    assert s.count(anchor) == 1, 'style anchor not found'
    s = s.replace(anchor, css)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Home.vue patched')
