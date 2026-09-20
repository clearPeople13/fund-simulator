# -*- coding: utf-8 -*-
"""Home.vue 详情弹窗加费率详情区（真实 fund_fees：申购/赎回阶梯/管理/托管），颗粒度可追溯"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) ref
old1 = """const detailDailyPnl = ref<any[]>([]) // 每日收益明细 [{date, nav, daily_return, shares, pnl}]"""
new1 = """const detailDailyPnl = ref<any[]>([]) // 每日收益明细 [{date, nav, daily_return, shares, pnl}]
const detailFees = ref<any>(null) // 基金真实费率（fund_fees）"""
assert s.count(old1) == 1, 'block1 not found'
s = s.replace(old1, new1)

# 2) 加载费率
old2 = """    // 基金基本信息（/api/funds/:code 查 funds 表，含经理/成立日期/基准；列表接口查 fund_universe 无这些字段）"""
new2 = """    // 费率详情（真实 fund_fees：申购/赎回阶梯/管理/托管）
    try {
      const feeRes = await axios.get('/api/ai/fund-fees', { params: { fund_code: code } })
      detailFees.value = (feeRes.data && feeRes.data.found) ? feeRes.data : null
    } catch (e4) {
      detailFees.value = null
    }
    // 基金基本信息（/api/funds/:code 查 funds 表，含经理/成立日期/基准；列表接口查 fund_universe 无这些字段）"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

# 3) 模板：基金信息后加费率详情
old3 = """          <div class="detail-section-title">基金信息</div>
          <div class="detail-info-grid" v-if="detailFund">
            <div class="detail-info-item">
              <span class="label">基金代码</span>
              <span class="value">{{ detailFund.code }}</span>
            </div>
            <div class="detail-info-item">
              <span class="label">基金类型</span>
              <span class="value">{{ detailFund.type || '—' }}</span>
            </div>
            <div class="detail-info-item">
              <span class="label">基金经理</span>
              <span class="value">{{ detailFund.manager || '—' }}</span>
            </div>
            <div class="detail-info-item">
              <span class="label">成立日期</span>
              <span class="value">{{ detailFund.inception_date || '—' }}</span>
            </div>
            <div class="detail-info-item benchmark-item">
              <span class="label">业绩基准</span>
              <span class="value benchmark">{{ detailFund.benchmark || '—' }}</span>
            </div>
          </div>
        </div>"""
new3 = """          <div class="detail-section-title">基金信息</div>
          <div class="detail-info-grid" v-if="detailFund">
            <div class="detail-info-item">
              <span class="label">基金代码</span>
              <span class="value">{{ detailFund.code }}</span>
            </div>
            <div class="detail-info-item">
              <span class="label">基金类型</span>
              <span class="value">{{ detailFund.type || '—' }}</span>
            </div>
            <div class="detail-info-item">
              <span class="label">基金经理</span>
              <span class="value">{{ detailFund.manager || '—' }}</span>
            </div>
            <div class="detail-info-item">
              <span class="label">成立日期</span>
              <span class="value">{{ detailFund.inception_date || '—' }}</span>
            </div>
            <div class="detail-info-item benchmark-item">
              <span class="label">业绩基准</span>
              <span class="value benchmark">{{ detailFund.benchmark || '—' }}</span>
            </div>
          </div>

          <div v-if="detailFees" class="detail-section-title" style="margin-top:18px">费率详情（真实费率）</div>
          <div v-if="detailFees" class="fee-grid">
            <div class="fee-item"><span class="fee-label">申购费率</span><span class="fee-value">{{ detailFees.buy_fee_pct }}%</span></div>
            <div class="fee-item"><span class="fee-label">管理费率（年）</span><span class="fee-value">{{ detailFees.manage_fee_pct }}%</span></div>
            <div class="fee-item"><span class="fee-label">托管费率（年）</span><span class="fee-value">{{ detailFees.custody_fee_pct }}%</span></div>
            <div class="fee-item"><span class="fee-label">销售服务费（年）</span><span class="fee-value">{{ detailFees.service_fee_pct }}%</span></div>
            <div class="fee-item fee-wide"><span class="fee-label">赎回费率（持有天数阶梯）</span>
              <span class="fee-value">
                <span v-for="(sc, si) in detailFees.sell_schedule" :key="si" class="fee-step">
                  {{ sc.days === 0 ? '≥1年' : '<' + sc.days + '天' }}：{{ sc.rate_pct }}%
                </span>
              </span>
            </div>
          </div>
        </div>"""
assert s.count(old3) == 1, 'block3 not found'
s = s.replace(old3, new3)

# 4) 样式（追加在 .act-desc 后）
old4 = """.act-desc { font-size: 12px; color: #64748b; margin-top: 2px; line-height: 1.5; }"""
new4 = """.act-desc { font-size: 12px; color: #64748b; margin-top: 2px; line-height: 1.5; }
.fee-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 10px; }
.fee-item { padding: 8px 12px; background: rgba(15,20,40,0.4); border-radius: 8px; }
.fee-wide { grid-column: 1 / -1; }
.fee-label { font-size: 12px; color: #94a3b8; display: block; margin-bottom: 4px; }
.fee-value { font-size: 13px; color: #e2e8f0; font-weight: 600; }
.fee-step { display: inline-block; margin: 2px 8px 2px 0; padding: 1px 8px; border-radius: 8px; background: rgba(99,102,241,0.12); color: #a5b4fc; font-size: 12px; }"""
assert s.count(old4) == 1, 'block4 not found'
s = s.replace(old4, new4)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Home.vue fee section patched')
