# -*- coding: utf-8 -*-
"""Home.vue 加 AI 经营成绩单（指标条）+ AI 决策轨迹（时间线）：用户通过数据看 AI 决策质量"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) ref 声明
old1 = """const pendingTxs = ref<any[]>([]) // 待确认订单（T+1）"""
new1 = """const pendingTxs = ref<any[]>([]) // 待确认订单（T+1）
const aiStats = ref<any>(null) // AI 经营成绩单
const aiActivity = ref<any[]>([]) // AI 决策轨迹"""
assert s.count(old1) == 1, 'block1 not found'
s = s.replace(old1, new1)

# 2) 加载 stats + activity
old2 = """    pendingTxs.value = (txRes.data && txRes.data.pending) || []"""
new2 = """    pendingTxs.value = (txRes.data && txRes.data.pending) || []
    // AI 经营成绩单 + 决策轨迹
    try {
      const statsRes = await axios.get('/api/ai/stats')
      aiStats.value = statsRes.data
      const actRes = await axios.get('/api/ai/activity', { params: { limit: 12 } })
      aiActivity.value = (actRes.data && actRes.data.list) || []
    } catch (e4) {
      console.error('加载AI经营数据失败:', e4)
    }"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

# 3) 模板：收益构成条后加 AI 经营成绩单
old3 = """      <div class="bd-item bd-total">
        <span class="bd-label">累计收益（已实现 + 浮动）</span>
        <span :class="pnlBreakdown.total >= 0 ? 'profit' : 'loss'">
          <template v-if="pnlBreakdown.total >= 0">+</template>¥{{ pnlBreakdown.total.toFixed(2) }}
        </span>
      </div>
    </div>"""
new3 = """      <div class="bd-item bd-total">
        <span class="bd-label">累计收益（已实现 + 浮动）</span>
        <span :class="pnlBreakdown.total >= 0 ? 'profit' : 'loss'">
          <template v-if="pnlBreakdown.total >= 0">+</template>¥{{ pnlBreakdown.total.toFixed(2) }}
        </span>
      </div>
    </div>

    <!-- AI 经营成绩单：AI 按现实基金操作法经营账户的量化成绩 -->
    <div v-if="aiStats" class="ai-score-card">
      <div class="score-head">
        <span class="score-title">🤖 AI 经营成绩单</span>
        <span class="score-sub">决策统计 · 全自动，用户只读</span>
      </div>
      <div class="score-grid">
        <div class="score-item">
          <div class="s-label">交易笔数</div>
          <div class="s-value">{{ aiStats.total_trades }} <small>（买{{ aiStats.buy_count }} / 卖{{ aiStats.sell_count }}）</small></div>
        </div>
        <div class="score-item">
          <div class="s-label">已实现盈亏</div>
          <div class="s-value" :class="aiStats.realized_pnl >= 0 ? 'profit' : 'loss'">
            <template v-if="aiStats.realized_pnl >= 0">+</template>¥{{ aiStats.realized_pnl.toFixed(2) }}
          </div>
        </div>
        <div class="score-item">
          <div class="s-label">卖出胜率</div>
          <div class="s-value">{{ aiStats.win_rate }}% <small>（{{ aiStats.win_count }}/{{ aiStats.realized_count }} 笔）</small></div>
        </div>
        <div class="score-item">
          <div class="s-label">平均持有</div>
          <div class="s-value">{{ aiStats.avg_hold_days }} 天</div>
        </div>
        <div class="score-item">
          <div class="s-label">风控执行</div>
          <div class="s-value">
            <span class="risk-tag">止损 {{ aiStats.stop_loss_count }}</span>
            <span class="risk-tag">止盈 {{ aiStats.stop_profit_count }}</span>
            <span class="risk-tag">减仓 {{ aiStats.reduce_count }}</span>
          </div>
        </div>
        <div class="score-item">
          <div class="s-label">建仓节奏</div>
          <div class="s-value">加仓 {{ aiStats.add_count }} 次 · 再平衡 {{ aiStats.rebalance_count }} 次</div>
        </div>
        <div class="score-item">
          <div class="s-label">盯盘规模</div>
          <div class="s-value">观察池 {{ aiStats.watchlist_count }} 只 · 已分析 {{ aiStats.analysis_rounds }} 轮</div>
        </div>
        <div class="score-item">
          <div class="s-label">累计手续费</div>
          <div class="s-value">¥{{ (aiStats.buy_fee + (0)).toFixed(2) }}</div>
        </div>
      </div>
    </div>"""
assert s.count(old3) == 1, 'block3 not found'
s = s.replace(old3, new3)

# 4) 模板：待确认订单卡前加 AI 决策轨迹
old4 = """    <!-- 待确认订单（T+1） -->"""
new4 = """    <!-- AI 决策轨迹 -->
    <div v-if="aiActivity.length" class="card">
      <div class="card-header">
        <h3>🧠 AI 决策轨迹</h3>
        <span class="badge info">最近 {{ aiActivity.length }} 条动作</span>
      </div>
      <div class="card-body">
        <div class="activity-list">
          <div v-for="(act, idx) in aiActivity" :key="idx" class="activity-item">
            <span class="act-time">{{ formatDate(act.time) }}</span>
            <span class="act-type" :class="'type-' + act.type">
              {{ act.type === 'buy' ? '买入' : act.type === 'sell' ? '卖出' : act.type === 'pending' ? '待确认' : act.type === 'risk' ? '风控' : act.type === 'analysis' ? '分析' : '系统' }}
            </span>
            <div class="act-body">
              <div class="act-title">{{ act.title }}{{ act.fund_name && !act.title.includes(act.fund_name) ? ' · ' + act.fund_name : '' }}</div>
              <div v-if="act.desc" class="act-desc">{{ act.desc }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 待确认订单（T+1） -->"""
assert s.count(old4) == 1, 'block4 not found'
s = s.replace(old4, new4)

# 5) 样式
anchor = """.pnl-breakdown { display: flex;"""
css = """.ai-score-card { margin: 14px 0 4px; padding: 16px 20px; background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(139,92,246,0.08)); border: 1px solid rgba(99,102,241,0.25); border-radius: 12px; }
.score-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.score-title { font-size: 15px; font-weight: 600; color: #e2e8f0; }
.score-sub { font-size: 12px; color: #64748b; }
.score-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.score-item { padding: 10px 12px; background: rgba(15,20,40,0.5); border-radius: 8px; }
.s-label { font-size: 12px; color: #94a3b8; margin-bottom: 4px; }
.s-value { font-size: 14px; font-weight: 600; color: #e2e8f0; }
.s-value small { font-weight: 400; color: #64748b; font-size: 11px; }
.risk-tag { display: inline-block; margin-right: 6px; padding: 1px 8px; border-radius: 8px; font-size: 11px; background: rgba(139,92,246,0.15); color: #a78bfa; }
.activity-list { display: flex; flex-direction: column; gap: 8px; }
.activity-item { display: flex; align-items: flex-start; gap: 12px; padding: 10px 12px; background: rgba(15,20,40,0.4); border-radius: 8px; }
.act-time { font-size: 12px; color: #64748b; white-space: nowrap; padding-top: 2px; }
.act-type { flex: 0 0 auto; padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.type-buy { background: rgba(16,185,129,0.15); color: #34d399; }
.type-sell { background: rgba(244,63,94,0.15); color: #f87171; }
.type-pending { background: rgba(245,158,11,0.15); color: #f59e0b; }
.type-risk { background: rgba(244,63,94,0.15); color: #fb7185; }
.type-analysis { background: rgba(99,102,241,0.15); color: #818cf8; }
.type-audit { background: rgba(148,163,184,0.15); color: #94a3b8; }
.type-order { background: rgba(6,182,212,0.15); color: #22d3ee; }
.act-body { flex: 1; min-width: 0; }
.act-title { font-size: 13px; color: #cbd5e1; }
.act-desc { font-size: 12px; color: #64748b; margin-top: 2px; line-height: 1.5; }
"""
assert s.count(anchor) == 1, 'style anchor not found'
s = s.replace(anchor, css)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Home.vue patched')
