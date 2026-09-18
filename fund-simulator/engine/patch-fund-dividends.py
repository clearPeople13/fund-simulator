# -*- coding: utf-8 -*-
"""FundDetail.vue 新增「历史分红」卡：分红总次数 + 最近分红列表（除息日/每份分红）"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\FundDetail.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) ref
old1 = """const fundReturns = ref([])"""
new1 = """const fundReturns = ref([])
const fundDividends = ref({ total: 0, list: [] })"""
assert s.count(old1) == 1, 'block1 not found'
s = s.replace(old1, new1)

# 2) 加载分红
old2 = """    fundReturns.value = returnsData

    fundInfo.value = {"""
new2 = """    fundReturns.value = returnsData

    // 历史分红明细
    try {
      const divRes = await axios.get(`/api/funds/${fundCode.value}/dividends`, { params: { limit: 30 } })
      if (divRes.data) fundDividends.value = divRes.data
    } catch (e) { fundDividends.value = { total: 0, list: [] } }

    fundInfo.value = {"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

# 3) 模板：最近净值卡后加分红卡
old3 = """      <!-- 最近净值 -->
      <a-card :bordered="false" title="最近净值">"""
new3 = """      <!-- 历史分红 -->
      <a-card :bordered="false" class="dividend-card">
        <template #title>
          <div class="block-title-inline">历史分红</div>
          <span class="returns-sub" v-if="fundDividends.total">累计 {{ fundDividends.total }} 次 · 数据由累计净值-单位净值推导</span>
          <span class="returns-sub" v-else>暂无分红记录（数据源未提供累计净值）</span>
        </template>
        <a-table
          v-if="fundDividends.list.length"
          :columns="dividendColumns"
          :data-source="fundDividends.list"
          :pagination="false"
          row-key="ex_date"
          size="small"
          class="dividend-table"
        />
        <div v-else class="returns-empty">该基金暂无分红记录</div>
      </a-card>

      <!-- 最近净值 -->
      <a-card :bordered="false" title="最近净值">"""
assert s.count(old3) == 1, 'block3 not found'
s = s.replace(old3, new3)

# 4) 列定义（加在 navColumns 附近）
old4 = """// AI分析"""
new4 = """// 历史分红列
const dividendColumns = [
  { title: '除息日', dataIndex: 'ex_date', width: 120 },
  { title: '每份分红', dataIndex: 'per_unit', width: 120, customRender: ({ text }) => '¥' + Number(text).toFixed(4) },
  { title: '类型', dataIndex: 'type', width: 80, customRender: ({ text }) => (text === 'CASH' ? '现金分红' : text) }
]

// AI分析"""
assert s.count(old4) == 1, 'block4 not found'
s = s.replace(old4, new4)

# 5) 样式（加进 style 块尾部）
old5 = """.block-title-inline { display: inline-block; font-size: 15px; font-weight: 600; color: var(--text, #e8ebff); }"""
new5 = """.block-title-inline { display: inline-block; font-size: 15px; font-weight: 600; color: var(--text, #e8ebff); }
.dividend-card { margin-top: 16px; }
.dividend-table :deep(.ant-table-thead > tr > th) { font-size: 12px; }
.dividend-table :deep(.ant-table-tbody > tr > td) { font-size: 13px; color: #cbd5e1; }"""
assert s.count(old5) == 1, 'block5 not found'
s = s.replace(old5, new5, 1)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('FundDetail dividends patched (注意检查样式插入位置)')
