# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue'
with io.open(p, 'r', encoding='utf-8') as f:
    c = f.read()

old = """// 查看基金详情（弹窗展示，真实数据）
const viewFundDetail = async (fund: any) => {
  const code = fund?.fund_code || fund?.code || fund?.fundCode
  if (!code) return
  detailVisible.value = true
  detailLoading.value = true
  detailTxs.value = transactions.value
    .filter((tx: any) => tx.fund_code === code)
    .slice()
    .sort((a: any, b: any) => String(a.raw || '').localeCompare(String(b.raw || '')))
  detailFund.value = { code, name: fund?.fund_name || fund?.name || code }
  try {
    // 净值历史（含日增长率，按日期匹配）
    const navRes = await axios.get(`/api/funds/${code}/nav`, { params: { limit: 120 } })
    const navRows = Array.isArray(navRes.data) ? navRes.data : []
    const map: Record<string, number> = {}
    for (const n of navRows) {
      if (n.nav_date && n.daily_return != null) map[n.nav_date] = n.daily_return
    }
    detailNavMap.value = map
    // 基金基本信息
    const fundRes = await axios.get('/api/funds', { params: { limit: 100 } })
    const info = ((fundRes.data && fundRes.data.data) || []).find((f: any) => f.fund_code === code)
    if (info) {
      detailFund.value = {
        code: info.fund_code,
        name: info.fund_name,
        type: info.fund_type,
        manager: info.manager,
        inception_date: info.inception_date,
        benchmark: info.benchmark
      }
    }
  } catch (error) {
    console.error('加载基金详情失败:', error)
  } finally {
    detailLoading.value = false
  }
}

"""
assert old in c, 'old viewFundDetail block not found'
c = c.replace(old, '', 1)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c)
print('OK 旧 viewFundDetail 已删除')
