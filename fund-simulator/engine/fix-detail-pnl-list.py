# -*- coding: utf-8 -*-
"""详情弹窗操作明细增加收益列（买入=剩余份额浮盈亏/卖出=已实现盈亏）+ 收益汇总条（平均成本法，与账户口径一致）"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) 重写 detailRows + 新增收益汇总
old1 = """// 操作明细列表：每笔交易的当日涨幅率 + 实际金额变动（买入=扣款支出，卖出=净到账）
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
}))"""
new1 = """// 操作明细列表：每笔交易的当日涨幅率 + 实际金额变动 + 收益（买入=剩余份额浮盈亏，卖出=已实现盈亏；平均成本法）
const detailRows = computed(() => {
  const txs = detailTxs.value.slice().sort((a: any, b: any) => String(a.raw || '').localeCompare(String(b.raw || '')))
  // 平均成本价 = total_cost / 当前份额（与账户口径一致）
  const hold = holdings.value.find((h: any) => h.fund_code === detailFund.value?.code)
  const avgCost = hold && hold.shares > 0 ? hold.total_cost / hold.shares : 0
  const curNav = hold ? hold.current_price : null
  // FIFO 扣减：每笔买入的剩余在持份额（卖出按买入先后扣减）
  const leftMap = new Map<string, number>()
  txs.forEach((t: any) => { if (t.action === '买入') leftMap.set(t.raw, Number(t.shares) || 0) })
  for (const t of txs) {
    if (t.action !== '卖出') continue
    let toSell = Number(t.shares) || 0
    for (const b of txs) {
      if (b.action !== '买入' || toSell <= 0) continue
      const left = leftMap.get(b.raw) || 0
      if (left <= 0) continue
      const cut = Math.min(left, toSell)
      leftMap.set(b.raw, left - cut)
      toSell -= cut
    }
  }
  return txs.map((tx: any) => {
    const day = String(tx.date).slice(0, 10).replace(/\\//g, '-')
    const navRow = detailNavList.value.find((n: any) => n.date === day)
    const isBuy = tx.action === '买入'
    const cash_change = isBuy ? -tx.amount : (tx.amount - (tx.fees || 0))
    let pnl: number | null = null
    let pnlRate: number | null = null
    let pnlTag = ''
    if (isBuy) {
      // 买入：剩余在持份额的浮盈亏（现价 - 平均成本）
      const left = leftMap.get(tx.raw) || 0
      pnl = curNav != null ? (curNav - avgCost) * left : null
      pnlRate = pnl != null && avgCost > 0 && left > 0 ? (pnl / (avgCost * left)) * 100 : null
      pnlTag = '浮'
    } else {
      // 卖出：已实现盈亏 = 净到账 - 卖出份额×平均成本（含费摊薄）
      const cost = avgCost * tx.shares
      pnl = cost > 0 ? (tx.amount - (tx.fees || 0)) - cost : null
      pnlRate = pnl != null && cost > 0 ? (pnl / cost) * 100 : null
      pnlTag = '实'
    }
    return { ...tx, day, daily_return: navRow ? navRow.daily_return : null, cash_change, pnl, pnl_rate: pnlRate, pnl_tag: pnlTag }
  })
})

// 收益汇总：已实现（卖出）/持有浮盈（买入剩余）/该基金合计
const detailPnlSummary = computed(() => {
  const rows = detailRows.value
  const realized = rows.filter((r: any) => r.action === '卖出').reduce((s: number, r: any) => s + (r.pnl ?? 0), 0)
  const floating = rows.filter((r: any) => r.action === '买入').reduce((s: number, r: any) => s + (r.pnl ?? 0), 0)
  return { realized, floating, total: realized + floating }
})"""
assert s.count(old1) == 1, 'block1 not found'
s = s.replace(old1, new1)

# 2) 表格加“收益/收益率”两列（表头）
old2 = """                  <th>手续费</th>
                  <th>当日涨幅</th>
                  <th>金额变动</th>"""
new2 = """                  <th>手续费</th>
                  <th>当日涨幅</th>
                  <th>金额变动</th>
                  <th>收益</th>
                  <th>收益率</th>"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

# 3) 行渲染加收益列
old3 = """                  <td :class="row.cash_change >= 0 ? 'profit' : 'loss'">
                    {{ row.cash_change >= 0 ? '+' : '' }}¥{{ Math.abs(row.cash_change).toFixed(2) }}
                    <span class="cash-note">{{ row.action === '买入' ? '支出' : '到账' }}</span>
                  </td>
                </tr>"""
new3 = """                  <td :class="row.cash_change >= 0 ? 'profit' : 'loss'">
                    {{ row.cash_change >= 0 ? '+' : '' }}¥{{ Math.abs(row.cash_change).toFixed(2) }}
                    <span class="cash-note">{{ row.action === '买入' ? '支出' : '到账' }}</span>
                  </td>
                  <td :class="row.pnl != null && row.pnl >= 0 ? 'profit' : 'loss'">
                    <template v-if="row.pnl != null">
                      {{ row.pnl >= 0 ? '+' : '' }}¥{{ Math.abs(row.pnl).toFixed(2) }}
                      <span class="pnl-tag" :class="row.pnl_tag === '实' ? 'realized' : 'floating'">{{ row.pnl_tag === '实' ? '已实现' : '浮动' }}</span>
                    </template>
                    <template v-else><span class="nav-date">—</span></template>
                  </td>
                  <td :class="row.pnl_rate != null && row.pnl_rate >= 0 ? 'profit' : 'loss'">
                    <template v-if="row.pnl_rate != null">{{ row.pnl_rate >= 0 ? '+' : '' }}{{ row.pnl_rate.toFixed(2) }}%</template>
                    <template v-else><span class="nav-date">—</span></template>
                  </td>
                </tr>"""
assert s.count(old3) == 1, 'block3 not found'
s = s.replace(old3, new3)

# 4) 表格后加收益汇总条
old4 = """            <div class="tx-note">金额变动：买入为扣款支出（含申购费）；卖出为净到账（已扣赎回费）。当日涨幅为该操作日基金净值涨跌幅。</div>"""
new4 = """            <div class="tx-note">金额变动：买入为扣款支出（含申购费）；卖出为净到账（已扣赎回费）。当日涨幅为该操作日基金净值涨跌幅。</div>
            <div class="pnl-summary">
              <span>收益汇总：</span>
              <span :class="detailPnlSummary.realized >= 0 ? 'profit' : 'loss'">已实现 {{ detailPnlSummary.realized >= 0 ? '+' : '' }}¥{{ Math.abs(detailPnlSummary.realized).toFixed(2) }}</span>
              <span class="sum-sep">·</span>
              <span :class="detailPnlSummary.floating >= 0 ? 'profit' : 'loss'">持有浮动 {{ detailPnlSummary.floating >= 0 ? '+' : '' }}¥{{ Math.abs(detailPnlSummary.floating).toFixed(2) }}</span>
              <span class="sum-sep">·</span>
              <span :class="detailPnlSummary.total >= 0 ? 'profit' : 'loss'" class="sum-total">该基金合计 {{ detailPnlSummary.total >= 0 ? '+' : '' }}¥{{ Math.abs(detailPnlSummary.total).toFixed(2) }}</span>
            </div>"""
assert s.count(old4) == 1, 'block4 not found'
s = s.replace(old4, new4)

# 5) 样式补充
old5 = """.tx-note { margin-top: 8px; font-size: 12px; color: var(--text-muted); line-height: 1.6; }"""
new5 = """.tx-note { margin-top: 8px; font-size: 12px; color: var(--text-muted); line-height: 1.6; }
.pnl-tag { font-size: 11px; margin-left: 4px; padding: 0 4px; border-radius: 4px; }
.pnl-tag.realized { background: rgba(129,140,248,0.15); color: #818cf8; }
.pnl-tag.floating { background: rgba(52,211,153,0.12); color: #34d399; }
.pnl-summary { margin-top: 10px; padding: 10px 14px; background: rgba(99,102,241,0.07); border-radius: 10px; font-size: 13px; display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.pnl-summary .sum-sep { color: var(--text-muted); }
.pnl-summary .sum-total { font-weight: 700; }"""
assert s.count(old5) == 1, 'block5 not found'
s = s.replace(old5, new5)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Home.vue patched')
