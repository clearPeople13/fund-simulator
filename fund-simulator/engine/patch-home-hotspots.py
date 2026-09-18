# -*- coding: utf-8 -*-
"""Home.vue：①新增“🔥 市场热点”卡（板块热度 + AI 点评 + 关联基金）②AI 决策轨迹支持 hotspot 类型"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) ref
old1 = """const aiActivity = ref<any[]>([]) // AI 决策轨迹"""
new1 = """const aiActivity = ref<any[]>([]) // AI 决策轨迹
const hotspots = ref<any>(null) // AI 市场热点分析"""
assert s.count(old1) == 1, 'block1 not found'
s = s.replace(old1, new1)

# 2) 加载热点
old2 = """      const actRes = await axios.get('/api/ai/activity', { params: { limit: 12 } })
      aiActivity.value = (actRes.data && actRes.data.list) || []"""
new2 = """      const actRes = await axios.get('/api/ai/activity', { params: { limit: 12 } })
      aiActivity.value = (actRes.data && actRes.data.list) || []
      // AI 市场热点
      try {
        const hpRes = await axios.get('/api/ai/hotspots')
        hotspots.value = hpRes.data || null
      } catch (e5) { hotspots.value = null }"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

# 3) 模板：AI 成绩单后加热点卡
old3 = """    <!-- AI 决策轨迹 -->
    <div v-if="aiActivity.length" class="card">"""
new3 = """    <!-- 市场热点（AI 关注分析） -->
    <div v-if="hotspots" class="card">
      <div class="card-header">
        <h3>🔥 市场热点 · AI 关注分析</h3>
        <span class="badge" :class="hotspotBadge(hotspots.overall)">{{ hotspots.overall }}</span>
      </div>
      <div class="card-body">
        <div class="hotspot-comment">
          <span class="hotspot-ai">AI 点评</span>
          <span>{{ hotspots.comment }}</span>
        </div>
        <div class="hotspot-list">
          <div v-for="(h, hi) in hotspots.hotspots" :key="hi" class="hotspot-item">
            <div class="hs-top">
              <span class="hs-theme">{{ h.theme }}</span>
              <span class="hs-score">热度 {{ h.hot_score }}</span>
            </div>
            <div class="hs-metrics">
              <span class="hs-m" :class="h.avg_day >= 0 ? 'profit' : 'loss'">日 <template v-if="h.avg_day > 0">+</template>{{ h.avg_day }}%</span>
              <span class="hs-m muted">周 <template v-if="h.avg_week > 0">+</template>{{ h.avg_week }}%</span>
              <span class="hs-m muted">月 <template v-if="h.avg_month > 0">+</template>{{ h.avg_month }}%</span>
              <span class="hs-count">{{ h.count }} 只</span>
            </div>
            <div v-if="h.related && h.related.length" class="hs-related">
              <span class="hs-rel-tag" v-for="(r, ri) in h.related" :key="ri">
                {{ r.held ? '🟢持仓' : '👀观察' }} {{ r.fund_name }}
                <span :class="r.day_return >= 0 ? 'profit' : 'loss'">{{ r.day_return >= 0 ? '+' : '' }}{{ r.day_return }}%</span>
              </span>
            </div>
            <div v-else class="hs-related muted">观察池暂无该主题基金，AI 不盲目追热点</div>
          </div>
        </div>
      </div>
    </div>

    <!-- AI 决策轨迹 -->
    <div v-if="aiActivity.length" class="card">"""
assert s.count(old3) == 1, 'block3 not found'
s = s.replace(old3, new3)

# 4) 轨迹类型支持 hotspot + 热点徽章函数
old4 = """            <span class="act-type" :class="'type-' + act.type">
              {{ act.type === 'buy' ? '买入' : act.type === 'sell' ? '卖出' : act.type === 'pending' ? '待确认' : act.type === 'risk' ? '风控' : act.type === 'analysis' ? '分析' : '系统' }}
            </span>"""
new4 = """            <span class="act-type" :class="'type-' + act.type">
              {{ act.type === 'buy' ? '买入' : act.type === 'sell' ? '卖出' : act.type === 'pending' ? '待确认' : act.type === 'risk' ? '风控' : act.type === 'hotspot' ? '热点' : act.type === 'analysis' ? '分析' : '系统' }}
            </span>"""
assert s.count(old4) == 1, 'block4 not found'
s = s.replace(old4, new4)

# 5) hotspotBadge 函数（加在操作明细前）
old5 = """// 操作明细列表：每笔交易的当日涨幅率 + 实际金额变动 + 收益（买入=剩余份额浮盈亏，卖出=已实现盈亏；平均成本法）"""
new5 = """// 热点状态徽章样式
const hotspotBadge = (o: string) => {
  if (o.includes('爆发')) return 'hotspot-hot'
  if (o.includes('启动')) return 'hotspot-warm'
  if (o.includes('走强')) return 'hotspot-mild'
  if (o.includes('退潮') || o.includes('防御')) return 'hotspot-cold'
  return 'hotspot-mild'
}

// 操作明细列表：每笔交易的当日涨幅率 + 实际金额变动 + 收益（买入=剩余份额浮盈亏，卖出=已实现盈亏；平均成本法）"""
assert s.count(old5) == 1, 'block5 not found'
s = s.replace(old5, new5)

# 6) 样式
old6 = """.type-audit { background: rgba(148,163,184,0.15); color: #94a3b8; }"""
new6 = """.type-audit { background: rgba(148,163,184,0.15); color: #94a3b8; }
.type-hotspot { background: rgba(251,191,36,0.15); color: #fbbf24; }
.hotspot-comment { display: flex; gap: 10px; align-items: flex-start; padding: 10px 14px; background: rgba(251,191,36,0.06); border: 1px solid rgba(251,191,36,0.18); border-radius: 10px; font-size: 13px; color: #cbd5e1; line-height: 1.6; margin-bottom: 12px; }
.hotspot-ai { flex: 0 0 auto; padding: 1px 10px; border-radius: 10px; background: rgba(251,191,36,0.15); color: #fbbf24; font-size: 12px; font-weight: 600; }
.hotspot-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 10px; }
.hotspot-item { padding: 12px 14px; background: rgba(15,20,40,0.4); border-radius: 10px; }
.hs-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.hs-theme { font-size: 14px; font-weight: 600; color: #e2e8f0; }
.hs-score { font-size: 11px; color: #fbbf24; background: rgba(251,191,36,0.1); padding: 1px 8px; border-radius: 8px; }
.hs-metrics { display: flex; gap: 10px; font-size: 12px; margin-bottom: 8px; }
.hs-m { color: #cbd5e1; }
.hs-count { margin-left: auto; color: #64748b; font-size: 11px; }
.hs-related { display: flex; flex-wrap: wrap; gap: 6px; font-size: 12px; }
.hs-rel-tag { padding: 2px 8px; border-radius: 8px; background: rgba(99,102,241,0.1); color: #a5b4fc; }
.badge.hotspot-hot { background: rgba(244,63,94,0.2); color: #fb7185; }
.badge.hotspot-warm { background: rgba(251,191,36,0.2); color: #fbbf24; }
.badge.hotspot-mild { background: rgba(52,211,153,0.15); color: #34d399; }
.badge.hotspot-cold { background: rgba(100,116,139,0.2); color: #94a3b8; }"""
assert s.count(old6) == 1, 'block6 not found'
s = s.replace(old6, new6)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Home.vue hotspots patched')
