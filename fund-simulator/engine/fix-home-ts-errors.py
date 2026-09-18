# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue'
with io.open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. 删除 router import 和实例
c = c.replace("""import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'""",
"""import { ref, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'""")
c = c.replace("""const router = useRouter()
const loading = ref<boolean>(true)""", """const loading = ref<boolean>(true)""")

# 2. 删除 closeDetail（Modal 由 v-model:open 控制）
old_close = """const closeDetail = () => {
  detailVisible.value = false
}

"""
assert old_close in c, 'closeDetail anchor not found'
c = c.replace(old_close, '')

# 3. growthOf 改为文本/颜色辅助函数（解决 TS null 收窄）
old_growth = """// 该交易日增长率（按交易日期匹配净值历史）
const growthOf = (tx: any): number | null => {
  const day = String(tx.date).slice(0, 10)
  const g = detailNavMap.value[day]
  return g !== undefined && g !== null ? g : null
}"""
new_growth = """// 该交易日增长率（按交易日期匹配净值历史）
const growthOf = (tx: any): number | null => {
  const day = String(tx.date).slice(0, 10)
  const g = detailNavMap.value[day]
  return g !== undefined && g !== null ? g : null
}
// 增长率文本（含符号），无数据返回 —
const growthText = (tx: any): string => {
  const g = growthOf(tx)
  return g != null ? (g >= 0 ? '+' : '') + g.toFixed(2) + '%' : '—'
}
// 增长率颜色
const growthCls = (tx: any): string => {
  const g = growthOf(tx)
  return g != null && g >= 0 ? 'profit' : 'loss'
}"""
assert old_growth in c, 'growth anchor not found'
c = c.replace(old_growth, new_growth)

# 4. 模板改用 growthText/growthCls
old_tpl = """                  <div class="tx-growth" :class="growthOf(tx) != null && growthOf(tx) >= 0 ? 'profit' : 'loss'">
                    {{ growthOf(tx) != null ? (growthOf(tx) >= 0 ? '+' : '') + growthOf(tx).toFixed(2) + '%' : '—' }}
                  </div>"""
new_tpl = """                  <div class="tx-growth" :class="growthCls(tx)">
                    {{ growthText(tx) }}
                  </div>"""
assert old_tpl in c, 'tpl anchor not found'
c = c.replace(old_tpl, new_tpl)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c)
print('OK: 修复 TS 错误')
