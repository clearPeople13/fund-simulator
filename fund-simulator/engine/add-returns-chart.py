# -*- coding: utf-8 -*-
import io

# ============ 1. 后端 routes.js 加 /funds/:code/returns ============
p1 = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\api\routes.js'
with io.open(p1, 'r', encoding='utf-8') as f:
    c1 = f.read()

anchor = """// 获取基金实时估值
router.get('/funds/:code/estimate', async (req, res) => {"""
new_route = """// 获取基金区间涨跌幅（支付宝式：近1月/近3月/近6月/近1年/近3年/成立来）
router.get('/funds/:code/returns', (req, res) => {
  const { code } = req.params;
  db.all(
    'SELECT nav_date, unit_nav FROM fund_nav WHERE fund_code = ? ORDER BY nav_date ASC',
    [code],
    (err, rows) => {
      if (err) { res.status(500).json({ error: err.message }); return; }
      if (!rows.length) { res.json({ fund_code: code, periods: [] }); return; }
      const last = rows.length - 1;
      const latestNav = rows[last].unit_nav;
      const latestDate = rows[last].nav_date;
      const calc = (idx) => (idx < 0 || idx >= rows.length ? null : (latestNav / rows[idx].unit_nav - 1) * 100);
      const defs = [
        { label: '近1月', idx: last - 22 },
        { label: '近3月', idx: last - 66 },
        { label: '近6月', idx: last - 132 },
        { label: '近1年', idx: last - 250 },
        { label: '近3年', idx: last - 750 },
        { label: '成立来', idx: 0 }
      ];
      const periods = defs.map(d => ({
        label: d.label,
        value: d.idx < 0 ? null : Number(calc(d.idx).toFixed(2)),
        start_date: (d.idx >= 0 && rows[d.idx]) ? rows[d.idx].nav_date : null,
        end_date: latestDate
      }));
      res.json({ fund_code: code, latest_nav: latestNav, latest_date: latestDate, periods });
    }
  );
});

// 获取基金实时估值
router.get('/funds/:code/estimate', async (req, res) => {"""
assert anchor in c1, 'routes.js anchor not found'
c1 = c1.replace(anchor, new_route, 1)
with io.open(p1, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c1)
print('OK routes.js +returns')

# ============ 2. 前端 FundDetail.vue ============
p2 = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\FundDetail.vue'
with io.open(p2, 'r', encoding='utf-8') as f:
    c2 = f.read()

# 2.1 script：加 fundReturns ref
old_script = "const fundInfo = ref(null)"
new_script = """const fundInfo = ref(null)
const fundReturns = ref([])"""
assert old_script in c2, 'script anchor1 not found'
c2 = c2.replace(old_script, new_script, 1)

# 2.2 loadFundDetail 中加载 returns
old_load = """    const navRows = Array.isArray(navRes.data) ? navRes.data : []

    fundInfo.value = {"""
new_load = """    const navRows = Array.isArray(navRes.data) ? navRes.data : []
    // 区间涨跌幅（支付宝式）
    let returnsData = []
    try {
      const retRes = await axios.get(`/api/funds/${fundCode.value}/returns`)
      if (retRes.data && Array.isArray(retRes.data.periods)) returnsData = retRes.data.periods
    } catch (e) { console.warn('加载区间涨跌幅失败:', e.message) }
    fundReturns.value = returnsData

    fundInfo.value = {"""
assert old_load in c2, 'script anchor2 not found'
c2 = c2.replace(old_load, new_load, 1)

# 2.3 计算函数：最大绝对值与条形宽度
old_fns = """// AI分析
const goToAIAnalysis = () => {"""
new_fns = """// 涨跌幅条形：正右负左，宽度按最大绝对值归一化（半幅 50%）
const returnsMax = (list) => Math.max(...list.map(p => Math.abs(p.value || 0)), 1e-6)
const retWidth = (v, max) => Math.min(Math.abs(v) / max * 50, 50)

// AI分析
const goToAIAnalysis = () => {"""
assert old_fns in c2, 'script anchor3 not found'
c2 = c2.replace(old_fns, new_fns, 1)

# 2.4 template：业绩基准卡片之后插入涨跌幅卡片
old_tpl = """      <!-- 最近净值 -->
      <a-card :bordered="false" title="最近净值">"""
new_tpl = """      <!-- 涨跌幅（支付宝式横向条形） -->
      <a-card :bordered="false" class="returns-card">
        <template #title>
          <div class="block-title-inline">涨跌幅</div>
          <span class="returns-sub" v-if="fundInfo.latest_nav_date">数据截至 {{ fundInfo.latest_nav_date }}</span>
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
assert old_tpl in c2, 'template anchor not found'
c2 = c2.replace(old_tpl, new_tpl, 1)

# 2.5 style：涨跌幅样式（插在最近净值表格样式前——找 style 尾部的 benchmark 样式后）
old_css = """/* 最近净值 */
"""
new_css = """/* 涨跌幅（支付宝式） */
.returns-card { margin-bottom: 20px; }
.block-title-inline { display: inline-block; font-size: 15px; font-weight: 600; color: var(--text, #e8ebff); }
.returns-sub { margin-left: 10px; font-size: 12px; color: #8b92b8; }
.returns-list { display: flex; flex-direction: column; gap: 14px; padding: 4px 8px 8px; }
.ret-row { display: flex; align-items: center; gap: 14px; }
.ret-label { width: 64px; font-size: 13px; color: #a5adcf; flex-shrink: 0; }
.ret-track { position: relative; flex: 1; height: 16px; background: rgba(255,255,255,0.04); border-radius: 4px; overflow: hidden; }
.ret-zero { position: absolute; top: 0; bottom: 0; left: 50%; width: 1px; background: rgba(139,146,184,0.5); z-index: 2; }
.ret-fill { position: absolute; top: 2px; bottom: 2px; border-radius: 3px; transition: width 0.3s; }
.ret-fill.up { background: linear-gradient(90deg, rgba(52,211,153,0.55), #34d399); }
.ret-fill.down { background: linear-gradient(270deg, rgba(248,113,113,0.55), #f87171); }
.ret-value { width: 84px; text-align: right; font-size: 13px; font-weight: 600; font-variant-numeric: tabular-nums; flex-shrink: 0; }
.returns-empty { padding: 12px 0; color: #8b92b8; font-size: 13px; }

/* 最近净值 */
"""
assert old_css in c2, 'css anchor not found'
c2 = c2.replace(old_css, new_css, 1)

with io.open(p2, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c2)
print('OK FundDetail.vue')
