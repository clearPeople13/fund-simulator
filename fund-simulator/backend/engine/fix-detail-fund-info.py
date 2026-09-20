# -*- coding: utf-8 -*-
"""Home.vue 详情弹窗基金信息改取 /api/funds/:code（funds 表，含 manager/benchmark；原 /api/funds 列表查 fund_universe 无这些字段导致显示 —）"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """    // 基金基本信息
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
    }"""
new = """    // 基金基本信息（/api/funds/:code 查 funds 表，含经理/成立日期/基准；列表接口查 fund_universe 无这些字段）
    try {
      const fundRes = await axios.get(`/api/funds/${code}`)
      const info = fundRes.data
      if (info && info.fund_code) {
        detailFund.value = {
          code: info.fund_code,
          name: info.fund_name,
          type: info.fund_type,
          manager: info.manager,
          inception_date: info.inception_date,
          benchmark: info.benchmark
        }
      }
    } catch (e3) {
      console.error('加载基金信息失败:', e3)
    }"""
assert s.count(old) == 1, 'block not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Home.vue patched')
