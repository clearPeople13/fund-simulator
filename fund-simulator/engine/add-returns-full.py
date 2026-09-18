# -*- coding: utf-8 -*-
import io

p2 = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\FundDetail.vue'
with io.open(p2, 'r', encoding='utf-8') as f:
    c2 = f.read()

# 1. script：fundReturns ref
old1 = "const fundInfo = ref(null)"
new1 = """const fundInfo = ref(null)
const fundReturns = ref([])"""
assert old1 in c2, 'anchor1'
c2 = c2.replace(old1, new1, 1)

# 2. loadFundDetail 加载 returns
old2 = """    const navRows = Array.isArray(navRes.data) ? navRes.data : []

    fundInfo.value = {"""
new2 = """    const navRows = Array.isArray(navRes.data) ? navRes.data : []
    // 区间涨跌幅（支付宝式）
    let returnsData = []
    try {
      const retRes = await axios.get(`/api/funds/${fundCode.value}/returns`)
      if (retRes.data && Array.isArray(retRes.data.periods)) returnsData = retRes.data.periods
    } catch (e) { console.warn('加载区间涨跌幅失败:', e.message) }
    fundReturns.value = returnsData

    fundInfo.value = {"""
assert old2 in c2, 'anchor2'
c2 = c2.replace(old2, new2, 1)

# 3. 计算函数
old3 = """// AI分析
const goToAIAnalysis = () => {"""
new3 = """// 涨跌幅条形：正右负左，宽度按最大绝对值归一化（半幅 50%）
const returnsMax = (list) => Math.max(...list.map(p => Math.abs(p.value || 0)), 1e-6)
const retWidth = (v, max) => Math.min(Math.abs(v) / max * 50, 50)

// AI分析
const goToAIAnalysis = () => {"""
assert old3 in c2, 'anchor3'
c2 = c2.replace(old3, new3, 1)

# 4. template：业绩基准卡片之后插入涨跌幅卡片
old4 = """      <!-- 最近净值 -->
      <a-card :bordered="false" title="最近净值">"""
new4 = """      <!-- 涨跌幅（支付宝式横向条形） -->
      <a-card :bordered="false" class="returns-card">
        <template #title>
          <div class="block-title-inline">涨跌幅</div>
          <span class="returns-sub" v-if="fundReturns.length">数据截至 {{ fundReturns[0].end_date }}</span>
        </template>
        <div v-if="fundReturns.length" class="returns-list">
          <div class="ret-row" v-for="p in fundReturns" :key="p.label">
            <span class="ret-label">{{ p.label }}</span>
            <div class="ret-track">
              <div class="ret-zero"></div>
              <div
                class="ret-fill"
                :class="p.value != null && p.value >= 0 ? 'up' : 'down'"
                :style="p.value != null ? { width: retWidth(p.value, returnsMax(fundReturns)) + '%', left: p.value >= 0 ? '50%' : 'auto', right: p.value >= 0 ? 'auto' : (50 - retWidth(p.value, returnsMax(fundReturns))) + '%' } : { display: 'none' }"
                :title="p.value != null && p.start_date ? (p.start_date + ' → ' + p.end_date) : '数据不足'"
              ></div>
            </div>
            <span class="ret-value" :class="p.value != null ? (p.value >= 0 ? 'profit' : 'loss') : ''">
              <template v-if="p.value != null">{{ p.value >= 0 ? '+' : '' }}{{ p.value }}%</template>
              <template v-else>—</template>
            </span>
          </div>
        </div>
        <div v-else class="returns-empty">暂无足够净值数据</div>
      </a-card>

      <!-- 最近净值 -->
      <a-card :bordered="false" title="最近净值">"""
assert old4 in c2, 'anchor4'
c2 = c2.replace(old4, new4, 1)

# 5. CSS（若已有涨跌幅样式则跳过）
if '/* 涨跌幅（支付宝式） */' not in c2:
    old5 = """.loss {
  color: #f87171;
  font-weight: 600;
}
</style>"""
    new5 = """.loss {
  color: #f87171;
  font-weight: 600;
}

/* 涨跌幅（支付宝式） */
.returns-card { margin-bottom: 20px; }
.block-title-inline { display: inline-block; font-size: 15px; font-weight: 600; color: var(--text, #e8ebff); }
.returns-sub { margin-left: 10px; font-size: 12px; color: #8b92b8; }
.returns-list { display: flex; flex-direction: column; gap: 14px; padding: 4px 8px 8px; }
.ret-row { display: flex; align-items: center; gap: 14px; }
.ret-label { width: 64px; font-size: 13px; color: #a5adcf; flex-shrink: 0; }
.ret-track { position: relative; flex: 1; height: 16px; background: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden; }
.ret-zero { position: absolute; top: 0; bottom: 0; left: 50%; width: 1px; background: rgba(139,146,184,0.5); z-index: 2; }
.ret-fill { position: absolute; top: 2px; bottom: 2px; border-radius: 3px; transition: width 0.3s; }
.ret-fill.up { background: linear-gradient(90deg, rgba(52,211,153,0.5), #34d399); }
.ret-fill.down { background: linear-gradient(270deg, rgba(248,113,113,0.5), #f87171); }
.ret-value { width: 84px; text-align: right; font-size: 13px; font-weight: 600; font-variant-numeric: tabular-nums; flex-shrink: 0; }
.returns-empty { padding: 12px 0; color: #8b92b8; font-size: 13px; }
</style>"""
    assert old5 in c2, 'anchor5'
    c2 = c2.replace(old5, new5, 1)
else:
    print('CSS 已存在，跳过')

with io.open(p2, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c2)
print('OK FundDetail.vue 完整更新')
