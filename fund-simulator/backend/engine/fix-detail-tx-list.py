# -*- coding: utf-8 -*-
"""基金详情弹窗增加“操作明细列表”：每笔交易的当日涨幅率 + 实际金额变动（买入扣款/卖出到账）"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) detailNavList 增加 daily_return
old1 = """    detailNavList.value = navRows
      .map((n: any) => ({ date: n.nav_date, nav: n.unit_nav }))
      .filter((n: any) => n.date && n.nav != null)
      .reverse()"""
new1 = """    detailNavList.value = navRows
      .map((n: any) => ({ date: n.nav_date, nav: n.unit_nav, daily_return: n.daily_return }))
      .filter((n: any) => n.date && n.nav != null)
      .reverse()"""
assert s.count(old1) == 1, 'block1 not found'
s = s.replace(old1, new1)

# 2) 新增 detailRows 计算（在 viewFundDetail 函数后）
old2 = """// 涨幅折线图（最近 120 交易日，以起点净值为 0 基准；买入▲绿/卖出▼红节点全部标记，悬浮显示买卖详情）"""
new2 = """// 操作明细列表：每笔交易的当日涨幅率 + 实际金额变动（买入=扣款支出，卖出=净到账）
const detailRows = computed(() => detailTxs.value.map((tx: any) => {
  const day = String(tx.date).slice(0, 10).replace(/\\//g, '-')
  const navRow = detailNavList.value.find((n: any) => n.date === day)
  const isBuy = tx.action === '买入'
  return {
    ...tx,
    day,
    daily_return: navRow ? navRow.daily_return : null,
    cash_change: isBuy ? -tx.amount : (tx.amount - (tx.fees || 0))
  }
}))

// 涨幅折线图（最近 120 交易日，以起点净值为 0 基准；买入▲绿/卖出▼红节点全部标记，悬浮显示买卖详情）"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

# 3) 弹窗模板：图表后加操作明细表格
old3 = """          <a-divider class="detail-divider" />

          <div class="detail-section-title">基金信息</div>"""
new3 = """          <a-divider class="detail-divider" />

          <div class="detail-section-title">操作明细（当日涨幅 · 实际金额变动）</div>
          <div class="detail-tx-table-wrap">
            <table class="detail-tx-table">
              <thead>
                <tr>
                  <th>时间</th>
                  <th>操作</th>
                  <th>份额</th>
                  <th>净值</th>
                  <th>金额</th>
                  <th>手续费</th>
                  <th>当日涨幅</th>
                  <th>金额变动</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in detailRows" :key="row.raw">
                  <td class="muted">{{ row.date }}</td>
                  <td>
                    <span class="tx-tag" :class="row.action === '买入' ? 'buy' : 'sell'">{{ row.action }}</span>
                  </td>
                  <td class="number">{{ Number(row.shares).toLocaleString() }}</td>
                  <td class="number">¥{{ Number(row.price).toFixed(4) }}</td>
                  <td class="number">¥{{ Number(row.amount).toFixed(2) }}</td>
                  <td class="number fee">¥{{ Number(row.fees || 0).toFixed(2) }}</td>
                  <td :class="(row.daily_return ?? 0) >= 0 ? 'profit' : 'loss'">
                    <template v-if="row.daily_return != null">{{ row.daily_return >= 0 ? '+' : '' }}{{ row.daily_return.toFixed(2) }}%</template>
                    <template v-else><span class="nav-date">待更新</span></template>
                  </td>
                  <td :class="row.cash_change >= 0 ? 'profit' : 'loss'">
                    {{ row.cash_change >= 0 ? '+' : '' }}¥{{ Math.abs(row.cash_change).toFixed(2) }}
                    <span class="cash-note">{{ row.action === '买入' ? '支出' : '到账' }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
            <div class="tx-note">金额变动：买入为扣款支出（含申购费）；卖出为净到账（已扣赎回费）。当日涨幅为该操作日基金净值涨跌幅。</div>
          </div>

          <a-divider class="detail-divider" />

          <div class="detail-section-title">基金信息</div>"""
assert s.count(old3) == 1, 'block3 not found'
s = s.replace(old3, new3)

# 4) 样式
old4 = """/* 基金详情弹窗 */"""
new4 = """.detail-tx-table-wrap { margin-top: 4px; overflow-x: auto; }
.detail-tx-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.detail-tx-table th { text-align: left; padding: 8px 10px; color: var(--text-muted); font-weight: 500; border-bottom: 1px solid var(--border); white-space: nowrap; }
.detail-tx-table td { padding: 8px 10px; color: var(--text); border-bottom: 1px solid rgba(255,255,255,0.04); white-space: nowrap; }
.detail-tx-table .number { font-variant-numeric: tabular-nums; }
.detail-tx-table .fee { color: #fbbf24; }
.tx-tag { display: inline-block; padding: 1px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; }
.tx-tag.buy { background: rgba(52,211,153,0.15); color: #34d399; }
.tx-tag.sell { background: rgba(248,113,113,0.15); color: #f87171; }
.cash-note { font-size: 11px; color: var(--text-muted); margin-left: 4px; }
.tx-note { margin-top: 8px; font-size: 12px; color: var(--text-muted); line-height: 1.6; }
.detail-tx-table .profit { color: #34d399; }
.detail-tx-table .loss { color: #f87171; }

/* 基金详情弹窗 */"""
assert s.count(old4) == 1, 'block4 not found'
s = s.replace(old4, new4)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Home.vue patched')
