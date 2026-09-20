# -*- coding: utf-8 -*-
"""Home.vue：todayPnl 为 null 时卡片/图表空态显示“待更新”，不再显示 0 或伪快照值"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) todayPnl computed：后端 null 且持仓均无今日盈亏 → 返回 null（待更新）
old1 = """const todayPnl = computed(() => {
  // 优先用后端 portfolio_daily 最新快照的当日盈亏（收盘按真实净值计算，覆盖盘中无当日净值场景）
  if (portfolio.value?.today_pnl != null) return portfolio.value.today_pnl
  // 回退：聚合持仓今日盈亏
  return holdings.value.reduce((sum, h) => {
    if (h.today_pnl !== null && h.today_pnl !== undefined) {
      return sum + h.today_pnl
    }
    return sum
  }, 0)
})"""
new1 = """const todayPnl = computed(() => {
  // 优先用后端 portfolio_daily 当日已确认快照（净值未公布时后端返回 null → 待更新）
  if (portfolio.value?.today_pnl != null) return portfolio.value.today_pnl
  // 回退：聚合持仓今日盈亏；若所有持仓今日盈亏均未更新（净值未公布），返回 null 表示待更新
  const sum = holdings.value.reduce((sum, h) => sum + (h.today_pnl ?? 0), 0)
  if (holdings.value.length > 0 && holdings.value.every(h => h.today_pnl === null || h.today_pnl === undefined)) return null
  return sum
})"""
assert s.count(old1) == 1, 'block1 not found'
s = s.replace(old1, new1)

# 2) 图表空态 sub 文案：null → 待更新
old2 = """      <p class="chart-empty-sub">今日盈亏 ${todayPnl.value >= 0 ? '+' : ''}¥${todayPnl.value.toFixed(2)}（当日买入按 T+1 确认，次日开始计盈亏）</p>"""
new2 = """      <p class="chart-empty-sub">今日盈亏 ${todayPnl.value === null ? '待更新（今日净值 21:30 公布后更新）' : (todayPnl.value >= 0 ? '+' : '') + '¥' + todayPnl.value.toFixed(2)}（当日买入按 T+1 确认，次日开始计盈亏）</p>"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

# 3) 今日盈亏卡片：null → 待更新
old3 = """      <div class="overview-card" :class="todayPnl >= 0 ? 'success' : 'danger'">
        <div class="card-icon">📈</div>
        <div class="card-content">
          <div class="card-label">今日盈亏</div>
          <div class="card-value">{{ todayPnl >= 0 ? '+' : '' }}¥{{ todayPnl.toFixed(2) }}</div>
        </div>
      </div>"""
new3 = """      <div class="overview-card" :class="todayPnl === null ? 'info' : (todayPnl >= 0 ? 'success' : 'danger')">
        <div class="card-icon">📈</div>
        <div class="card-content">
          <div class="card-label">今日盈亏</div>
          <div class="card-value">
            <template v-if="todayPnl === null"><span class="nav-date">待更新</span></template>
            <template v-else>{{ todayPnl >= 0 ? '+' : '' }}¥{{ todayPnl.toFixed(2) }}</template>
          </div>
          <div class="card-sub" v-if="todayPnl === null">今日净值 21:30 公布后更新</div>
        </div>
      </div>"""
assert s.count(old3) == 1, 'block3 not found'
s = s.replace(old3, new3)

# 4) 持仓明细“今日盈亏”待更新文案补充说明
old4 = """                  <template v-else><span class="nav-date">净值待更新</span></template>"""
new4 = """                  <template v-else><span class="nav-date">净值待更新</span><span class="t1-tag" title="今日净值 21:30 公布后更新">今日</span></template>"""
assert s.count(old4) == 1, 'block4 not found'
s = s.replace(old4, new4)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Home.vue patched')
