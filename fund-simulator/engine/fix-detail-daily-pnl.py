# -*- coding: utf-8 -*-
"""Home.vue 详情弹窗新增“收益明细”区块：每日 日期/当日盈亏金额/当日涨幅 表格（操作明细保留不动）"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) 声明 detailDailyPnl
old1 = """const detailTxs = ref<any[]>([])
const detailNavList = ref<any[]>([]) // 升序 [{date, nav}]"""
new1 = """const detailTxs = ref<any[]>([])
const detailNavList = ref<any[]>([]) // 升序 [{date, nav}]
const detailDailyPnl = ref<any[]>([]) // 每日收益明细 [{date, nav, daily_return, shares, pnl}]"""
assert s.count(old1) == 1, 'block1 not found'
s = s.replace(old1, new1)

# 2) viewFundDetail 加载每日收益明细
old2 = """    // 基金基本信息
    const fundRes = await axios.get('/api/funds', { params: { limit: 100 } })"""
new2 = """    // 每日收益明细（日期/当日涨幅/当日盈亏金额）
    try {
      const dailyPnlRes = await axios.get('/api/ai/fund-daily-pnl', { params: { fund_code: code } })
      detailDailyPnl.value = (dailyPnlRes.data && dailyPnlRes.data.data) || []
    } catch (e2) {
      detailDailyPnl.value = []
    }
    // 基金基本信息
    const fundRes = await axios.get('/api/funds', { params: { limit: 100 } })"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

# 3) 模板：涨幅图后插入“收益明细”区块（操作明细之前）
old3 = """          <a-divider class="detail-divider" />

          <div class="detail-section-title">操作明细（当日涨幅 · 实际金额变动）</div>"""
new3 = """          <a-divider class="detail-divider" />

          <div class="detail-section-title">收益明细（每日盈亏）</div>
          <div class="detail-tx-table-wrap">
            <table class="detail-tx-table">
              <thead>
                <tr>
                  <th>日期</th>
                  <th>当日盈亏金额</th>
                  <th>当日涨幅</th>
                  <th>当日持有份额</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in detailDailyPnl" :key="row.date">
                  <td class="muted">{{ row.date }}</td>
                  <td :class="row.pnl >= 0 ? 'profit' : 'loss'">
                    <template v-if="row.pnl !== 0 || row.shares === 0">{{ row.pnl >= 0 ? '+' : '' }}¥{{ Math.abs(row.pnl).toFixed(2) }}</template>
                    <template v-else><span class="nav-date">T+1</span></template>
                  </td>
                  <td :class="(row.daily_return ?? 0) >= 0 ? 'profit' : 'loss'">
                    {{ row.daily_return >= 0 ? '+' : '' }}{{ row.daily_return.toFixed(2) }}%
                  </td>
                  <td class="number">{{ row.shares.toLocaleString() }} 份</td>
                </tr>
              </tbody>
            </table>
            <div class="tx-note">当日盈亏金额 = 当日收盘持有份额 ×（当日净值 − 前一日净值）；买入当日 T+1 无收益。今日净值公布后自动更新。</div>
          </div>

          <a-divider class="detail-divider" />

          <div class="detail-section-title">操作明细（当日涨幅 · 实际金额变动）</div>"""
assert s.count(old3) == 1, 'block3 not found'
s = s.replace(old3, new3)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Home.vue patched')
