# -*- coding: utf-8 -*-
import io, re

path = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue'
with io.open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. 今日盈亏列：pendingConfirm +¥0.00 T+1；null → 净值待更新
old3 = '''                  <template v-if="holding.today_pnl !== null">
                    {{ holding.today_pnl >= 0 ? '+' : '' }}¥{{ holding.today_pnl.toFixed(2) }}
                    <span v-if="holding.pending_confirm" class="t1-tag" title="T+1 规则：当日买入按当日收盘净值确认，次日开始计算收益">T+1</span>
                  </template>
                  <template v-else>--</template>'''
new3 = '''                  <template v-if="holding.pending_confirm">
                    +¥0.00
                    <span class="t1-tag" title="T+1 规则：当日买入按当日收盘净值确认，次日开始计算收益">T+1</span>
                  </template>
                  <template v-else-if="holding.today_pnl !== null">
                    {{ holding.today_pnl >= 0 ? '+' : '' }}¥{{ holding.today_pnl.toFixed(2) }}
                  </template>
                  <template v-else><span class="nav-date">净值待更新</span></template>'''
if old3 not in c:
    print('锚点3未找到')
    raise SystemExit(1)
c = c.replace(old3, new3)

# 2. todayDateStr 方法
old4 = 'const isSameLocalDay = (utcStr: string): boolean => {'
new4 = '''// 本地今天 YYYY-MM-DD（模板展示用）
const todayDateStr = (): string => {
  const d = new Date(); const m = String(d.getMonth() + 1).padStart(2, '0'); const day = String(d.getDate()).padStart(2, '0'); return d.getFullYear() + '-' + m + '-' + day
}
const isSameLocalDay = (utcStr: string): boolean => {'''
if old4 not in c:
    print('锚点4未找到')
    raise SystemExit(1)
c = c.replace(old4, new4)

with io.open(path, 'w', encoding='utf-8', newline='') as f:
    f.write(c)
print('Home.vue 今日盈亏列与 todayDateStr 完成')
