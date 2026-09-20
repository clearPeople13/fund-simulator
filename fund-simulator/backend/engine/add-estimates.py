# -*- coding: utf-8 -*-
import io

# ============ 1. 后端 routes.js：批量持仓估值接口 ============
p1 = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\api\routes.js'
c1 = io.open(p1, encoding='utf-8').read()
anchor1 = """// 投资组合相关路由

// 获取投资组合列表"""
new1 = """// 批量获取持仓基金实时估值（预估今日涨幅）
router.get('/portfolio/estimates', async (req, res) => {
  const codes = String(req.query.codes || '').split(',').map(s => s.trim()).filter(Boolean);
  if (!codes.length) { res.json({}); return; }
  const out = {};
  for (const code of codes) {
    try {
      const e = await fetcher.getRealTimeEstimate(code);
      out[code] = e ? {
        estimate_return: e.estimate_return,
        estimate_time: e.estimate_time || '',
        estimate_available: !!e.estimate_available,
        estimate_nav: e.estimate_nav || 0
      } : null;
    } catch (err) {
      out[code] = null;
    }
    await new Promise(r => setTimeout(r, 120));
  }
  res.json(out);
});

// 投资组合相关路由

// 获取投资组合列表"""
assert c1.count(anchor1) == 1, 'routes anchor count=%d' % c1.count(anchor1)
c1 = c1.replace(anchor1, new1, 1)
io.open(p1, 'w', encoding='utf-8', newline='\n').write(c1)
print('OK routes.js +portfolio/estimates')

# ============ 2. 前端 Home.vue ============
p2 = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue'
c2 = io.open(p2, encoding='utf-8').read()

# 2.1 loadAllData 中加载持仓详情后调用 loadEstimates
old_call = """    // 加载持仓详情
    await loadHoldingsDetail()
    """
new_call = """    // 加载持仓详情
    await loadHoldingsDetail()

    // 加载持仓基金今日预估涨幅（盘中估值）
    await loadEstimates()
    """
assert c2.count(old_call) == 1, 'load call anchor'
c2 = c2.replace(old_call, new_call, 1)

# 2.2 新增 loadEstimates 函数（放在 loadHoldingsDetail 之后）
old_fn = """// 基金详情弹窗（持仓明细/观察池 → 弹窗：操作记录时间线 + 基金信息，不再跳页）"""
new_fn = """// 加载持仓基金今日预估涨幅（/api/portfolio/estimates 批量估值，合并到 holdings）
const loadEstimates = async () => {
  try {
    const codes = holdings.value.map((h: any) => h.fund_code).join(',')
    if (!codes) return
    const res = await axios.get('/api/portfolio/estimates', { params: { codes } })
    const map = res.data || {}
    holdings.value = holdings.value.map((h: any) => {
      const e = map[h.fund_code]
      return {
        ...h,
        estimate_return: e && e.estimate_return !== null && e.estimate_return !== undefined ? e.estimate_return : null,
        estimate_time: e && e.estimate_time ? e.estimate_time : '',
        estimate_available: !!(e && e.estimate_available)
      }
    })
  } catch (err) {
    console.warn('加载预估涨幅失败:', err.message)
  }
}

// 基金详情弹窗（持仓明细/观察池 → 弹窗：操作记录时间线 + 基金信息，不再跳页）"""
assert c2.count(old_fn) == 1, 'fn anchor'
c2 = c2.replace(old_fn, new_fn, 1)

# 2.3 表格表头加列
old_th = """                <th>日涨跌</th>
                <th>今日盈亏</th>"""
new_th = """                <th>日涨跌</th>
                <th>预估今日</th>
                <th>今日盈亏</th>"""
assert c2.count(old_th) == 1, 'th anchor'
c2 = c2.replace(old_th, new_th, 1)

# 2.4 表格单元格加列（在日涨跌 td 之后、今日盈亏 td 之前）
old_td = """                  <template v-else>--</template>
                </td>
                <td :class="holding.today_pnl >= 0 ? 'profit' : 'loss'">"""
new_td = """                  <template v-else>--</template>
                </td>
                <td :class="(holding.estimate_return ?? 0) >= 0 ? 'profit' : 'loss'">
                  <template v-if="holding.estimate_available && holding.estimate_return !== null">
                    {{ holding.estimate_return >= 0 ? '+' : '' }}{{ holding.estimate_return.toFixed(2) }}%
                    <a-tooltip v-if="holding.estimate_time" :title="'估值时间 ' + holding.estimate_time">
                      <span class="nav-date est-time">{{ holding.estimate_time.slice(11, 16) }}</span>
                    </a-tooltip>
                  </template>
                  <template v-else><span class="nav-date">—</span></template>
                </td>
                <td :class="holding.today_pnl >= 0 ? 'profit' : 'loss'">"""
assert c2.count(old_td) == 1, 'td anchor'
c2 = c2.replace(old_td, new_td, 1)

# 2.5 CSS：est-time 样式
old_css = """.t1-tag {
  display: inline-block;
  margin-left: 4px;
  padding: 0 5px;
  font-size: 10px;
  line-height: 16px;
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.12);
  border-radius: 3px;
}"""
new_css = """.t1-tag {
  display: inline-block;
  margin-left: 4px;
  padding: 0 5px;
  font-size: 10px;
  line-height: 16px;
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.12);
  border-radius: 3px;
}
.est-time {
  margin-left: 4px;
  cursor: help;
}"""
assert c2.count(old_css) == 1, 'css anchor'
c2 = c2.replace(old_css, new_css, 1)

io.open(p2, 'w', encoding='utf-8', newline='\n').write(c2)
print('OK Home.vue 预估今日列')
