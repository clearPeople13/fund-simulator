# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Funds.vue'
c = io.open(p, encoding='utf-8').read()

# 1. 类型选项 → 全市场基金库四大类
old = """// 基金类型选项
const fundTypes = [
  { value: '', label: '全部类型' },
  { value: '股票型', label: '股票型' },
  { value: '混合型', label: '混合型' },
  { value: '债券型', label: '债券型' },
  { value: '指数型', label: '指数型' },
  { value: '货币型', label: '货币型' }
]"""
new = """// 基金类型选项（全市场基金库：股票型/混合型/指数型/QDII）
const fundTypes = [
  { value: '', label: '全部类型' },
  { value: '股票型', label: '股票型' },
  { value: '混合型', label: '混合型' },
  { value: '指数型', label: '指数型' },
  { value: 'QDII', label: 'QDII' }
]"""
assert c.count(old) == 1, 'types %d' % c.count(old)
c = c.replace(old, new, 1)

# 2. 类型颜色
old2 = """  const map = {
    '股票型': 'red',
    '混合型': 'orange',
    '债券型': 'green',
    '指数型': 'blue',
    '货币型': 'default'
  }"""
new2 = """  const map = {
    '股票型': 'red',
    '混合型': 'orange',
    '指数型': 'blue',
    'QDII': 'purple'
  }"""
assert c.count(old2) == 1, 'color %d' % c.count(old2)
c = c.replace(old2, new2, 1)

# 3. 本地过滤 → 服务端分页
old3 = """// 过滤后的基金列表
const filteredFunds = computed(() => {
  let result = [...funds.value]

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(fund =>
      fund.fund_code.includes(query) ||
      fund.fund_name.toLowerCase().includes(query)
    )
  }

  if (selectedType.value) {
    result = result.filter(fund => (fund.fund_type || '').startsWith(selectedType.value))
  }

  total.value = result.length
  return result.slice((currentPage.value - 1) * pageSize.value, currentPage.value * pageSize.value)
})"""
new3 = """// 基金列表数据（服务端分页/搜索/类型过滤）
const filteredFunds = computed(() => funds.value)"""
assert c.count(old3) == 1, 'filtered %d' % c.count(old3)
c = c.replace(old3, new3, 1)

# 4. 加载函数 → 服务端分页
old4 = """// 加载基金列表（真实数据）
const loadFunds = async () => {
  try {
    loading.value = true
    const response = await axios.get('/api/funds', { params: { limit: 100 } })
    funds.value = (response.data && response.data.data) || []
    total.value = funds.value.length
  } catch (error) {
    console.error('加载基金列表失败:', error)
    funds.value = []
  } finally {
    loading.value = false
  }
}"""
new4 = """// 加载基金列表（全市场基金库，服务端分页）
const loadFunds = async () => {
  try {
    loading.value = true
    const response = await axios.get('/api/funds', {
      params: {
        page: currentPage.value,
        limit: pageSize.value,
        type: selectedType.value || undefined,
        keyword: searchQuery.value || undefined,
        sort: 'r6m'
      }
    })
    funds.value = (response.data && response.data.data) || []
    total.value = (response.data && response.data.pagination && response.data.pagination.total) || 0
  } catch (error) {
    console.error('加载基金列表失败:', error)
    funds.value = []
  } finally {
    loading.value = false
  }
}"""
assert c.count(old4) == 1, 'load %d' % c.count(old4)
c = c.replace(old4, new4, 1)

# 5. 页码变化 → 重新加载
old5 = """// 页码变化
const handleCurrentChange = (page) => {
  currentPage.value = page
}"""
new5 = """// 页码变化 → 服务端重新加载
const handleCurrentChange = (page) => {
  currentPage.value = page
  loadFunds()
}

// 搜索/类型变化 → 回到第 1 页重新加载
const handleFilterChange = () => {
  currentPage.value = 1
  loadFunds()
}"""
assert c.count(old5) == 1, 'page %d' % c.count(old5)
c = c.replace(old5, new5, 1)

# 6. 模板：输入框/选择器绑定过滤事件 + hero 文案
old6 = """          <a-input
            v-model:value="searchQuery"
            placeholder="搜索基金代码或名称"
            allow-clear
          >"""
new6 = """          <a-input
            v-model:value="searchQuery"
            placeholder="搜索基金代码或名称"
            allow-clear
            @change="handleFilterChange"
          >"""
assert c.count(old6) == 1, 'input %d' % c.count(old6)
c = c.replace(old6, new6, 1)

old7 = """          <a-select v-model:value="selectedType" placeholder="选择基金类型" style="width: 100%">"""
new7 = """          <a-select v-model:value="selectedType" placeholder="选择基金类型" style="width: 100%" @change="handleFilterChange">"""
assert c.count(old7) == 1, 'select %d' % c.count(old7)
c = c.replace(old7, new7, 1)

old8 = """          <span class="hero-stat-label">只基金 · 实时净值</span>"""
new8 = """          <span class="hero-stat-label">只基金 · 全市场基金库</span>"""
assert c.count(old8) == 1, 'hero %d' % c.count(old8)
c = c.replace(old8, new8, 1)

# 7. 搜索栏提示更新
old9 = """            <a-tag>共 {{ total }} 只基金</a-tag>"""
new9 = """            <a-tag>共 {{ total }} 只 · AI 选基范围即全市场</a-tag>"""
assert c.count(old9) == 1, 'tag %d' % c.count(old9)
c = c.replace(old9, new9, 1)

io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
