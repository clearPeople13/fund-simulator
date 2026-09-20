# -*- coding: utf-8 -*-
"""FundDetail.vue：涨跌幅卡后新增「同类排名」卡（全市场同类型基金区间涨幅百分位 + 条形）"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\FundDetail.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) ref
old1 = """const fundDividends = ref({ total: 0, list: [] })"""
new1 = """const fundDividends = ref({ total: 0, list: [] })
const fundRank = ref(null)"""
assert s.count(old1) == 1, 'block1 not found'
s = s.replace(old1, new1)

# 2) 加载排名（在分红加载后）
old2 = """    // 历史分红明细
    try {
      const divRes = await axios.get(`/api/funds/${fundCode.value}/dividends`, { params: { limit: 30 } })
      if (divRes.data) fundDividends.value = divRes.data
    } catch (e) { fundDividends.value = { total: 0, list: [] } }
"""
new2 = """    // 历史分红明细
    try {
      const divRes = await axios.get(`/api/funds/${fundCode.value}/dividends`, { params: { limit: 30 } })
      if (divRes.data) fundDividends.value = divRes.data
    } catch (e) { fundDividends.value = { total: 0, list: [] } }

    // 同类排名
    try {
      const rankRes = await axios.get(`/api/funds/${fundCode.value}/rank`)
      if (rankRes.data && rankRes.data.found) fundRank.value = rankRes.data
    } catch (e) { fundRank.value = null }
"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

# 3) 模板：涨跌幅卡后加同类排名卡
old3 = """      <!-- 最近净值 -->
      <a-card :bordered="false" title="最近净值">"""
new3 = """      <!-- 同类排名 -->
      <a-card :bordered="false" class="rank-card" v-if="fundRank">
        <template #title>
          <div class="block-title-inline">同类排名</div>
          <span class="returns-sub">全市场 {{ fundRank.fund_type }}基金 · 区间涨幅百分位（值越小越靠前）</span>
        </template>
        <div class="rank-list">
          <div class="rank-row" v-for="r in fundRank.ranks" :key="r.key">
            <span class="rank-label">{{ r.label }}</span>
            <div class="rank-track">
              <div class="rank-bar" :class="r.percentile <= 25 ? 'top' : r.percentile <= 60 ? 'mid' : 'bot'"
                   :style="{ width: (100 - r.percentile) + '%' }"></div>
              <div class="rank-marker" :style="{ left: r.percentile + '%' }"></div>
            </div>
            <span class="rank-value" :class="r.percentile <= 25 ? 'top' : r.percentile <= 60 ? 'mid' : 'bot'">
              {{ r.rank }}/{{ r.total }} · 前 {{ r.percentile }}%
            </span>
          </div>
        </div>
      </a-card>

      <!-- 最近净值 -->
      <a-card :bordered="false" title="最近净值">"""
assert s.count(old3) == 1, 'block3 not found'
s = s.replace(old3, new3)

# 4) 样式（加在 dividend 样式后）
old4 = """.dividend-table :deep(.ant-table-tbody > tr > td) { font-size: 13px; color: #cbd5e1; }"""
new4 = """.dividend-table :deep(.ant-table-tbody > tr > td) { font-size: 13px; color: #cbd5e1; }
.rank-card { margin-top: 16px; }
.rank-list { display: flex; flex-direction: column; gap: 12px; }
.rank-row { display: flex; align-items: center; gap: 12px; }
.rank-label { flex: 0 0 56px; font-size: 13px; color: #94a3b8; }
.rank-track { position: relative; flex: 1; height: 8px; border-radius: 6px; background: rgba(148,163,184,0.15); }
.rank-bar { position: absolute; left: 0; top: 0; height: 100%; border-radius: 6px; opacity: 0.85; }
.rank-bar.top { background: linear-gradient(90deg, #34d399, #10b981); }
.rank-bar.mid { background: linear-gradient(90deg, #fbbf24, #f59e0b); }
.rank-bar.bot { background: linear-gradient(90deg, #f87171, #ef4444); }
.rank-marker { position: absolute; top: -3px; width: 3px; height: 14px; background: #e2e8f0; border-radius: 2px; }
.rank-value { flex: 0 0 auto; font-size: 12px; font-weight: 600; min-width: 120px; text-align: right; }
.rank-value.top { color: #34d399; }
.rank-value.mid { color: #fbbf24; }
.rank-value.bot { color: #f87171; }"""
assert s.count(old4) == 1, 'block4 not found'
s = s.replace(old4, new4)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('FundDetail rank card patched')
