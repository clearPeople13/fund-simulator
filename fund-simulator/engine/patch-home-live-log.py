# -*- coding: utf-8 -*-
"""Home.vue：新增「📡 AI 实时控制台」—— EventSource 订阅 /api/ai/stream，AI 思考/分析/下单实时滚动"""
import io

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) ref
old1 = """const aiCompare = ref<any>(null) // 双经理经营对比"""
new1 = """const aiCompare = ref<any>(null) // 双经理经营对比
const liveLogs = ref<any[]>([]) // AI 实时日志流
const liveStatus = ref<'connecting'|'live'|'closed'>('connecting')"""
assert s.count(old1) == 1, 'block1'
s = s.replace(old1, new1)

# 2) EventSource 初始化（onMounted 里，在 loadHomeData 后）
old2 = """onMounted(() => {
  loadAllData()
})"""
new2 = """// AI 实时日志流（SSE）
const startLiveStream = () => {
  try {
    const es = new EventSource('/api/ai/stream')
    es.onopen = () => { liveStatus.value = 'live' }
    es.onerror = () => { liveStatus.value = 'closed' }
    es.onmessage = (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data)
        liveLogs.value.unshift(data)
        if (liveLogs.value.length > 60) liveLogs.value.length = 60
      } catch (e) { /* ignore */ }
    }
  } catch (e) { liveStatus.value = 'closed' }
}

onMounted(() => {
  loadHomeData()
  startLiveStream()
})"""
assert s.count(old2) == 1, 'block2'
s = s.replace(old2, new2)

# 3) 图标/颜色 helper
old3 = """// 热点状态徽章样式"""
new3 = """// 实时日志类型图标/颜色
const liveIcon = (t: string) => ({
  phase: '🧠', discover: '🔍', signal: '📊', order: '📈', block: '🚫', system: '⚙️'
} as any)[t] || '•'
const liveColor = (t: string) => ({
  phase: 'color:#a78bfa', discover: 'color:#60a5fa', signal: 'color:#94a3b8',
  order: 'color:#34d399', block: 'color:#f87171', system: 'color:#64748b'
} as any)[t] || 'color:#94a3b8'
const liveTime = (iso: string) => {
  try { return new Date(iso).toLocaleTimeString('zh-CN', { hour12: false }) } catch (e) { return '' }
}

// 热点状态徽章样式"""
assert s.count(old3) == 1, 'block3'
s = s.replace(old3, new3)

# 4) 模板：决策轨迹前加实时控制台
old4 = """    <!-- AI 决策轨迹 -->"""
new4 = """    <!-- AI 实时控制台（SSE 日志流） -->
    <div class="card">
      <div class="card-header">
        <h3>📡 AI 实时控制台</h3>
        <span class="muted">
          <span :style="{ color: liveStatus === 'live' ? '#34d399' : '#f87171' }">●</span>
          {{ liveStatus === 'live' ? '已连接' : liveStatus === 'connecting' ? '连接中…' : '已断开' }}
          · AI 思考/分析/下单实时推送
        </span>
      </div>
      <div class="card-body">
        <div class="live-log-box">
          <div v-if="liveLogs.length === 0" class="live-empty">等待 AI 下次分析（交易日盘中每 30 分钟 / 收盘后）…</div>
          <div v-for="(log, i) in liveLogs" :key="i" class="live-log-line">
            <span class="live-time">{{ liveTime(log.time) }}</span>
            <span :style="{ color: liveColor(log.type) }">{{ liveIcon(log.type) }}</span>
            <span class="live-msg">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- AI 决策轨迹 -->"""
assert s.count(old4) == 1, 'block4'
s = s.replace(old4, new4)

# 5) 样式
old5 = """.muted { color: #64748b; font-size: 12px; font-weight: 400; }"""
new5 = """.muted { color: #64748b; font-size: 12px; font-weight: 400; }
.live-log-box { background: rgba(0,0,0,0.25); border: 1px solid rgba(99,102,241,0.18); border-radius: 10px; padding: 10px 12px; max-height: 280px; overflow-y: auto; font-family: 'Consolas', 'Monaco', monospace; font-size: 12px; }
.live-empty { color: #64748b; text-align: center; padding: 24px 0; font-family: sans-serif; }
.live-log-line { display: flex; gap: 8px; align-items: baseline; padding: 3px 0; border-bottom: 1px dashed rgba(148,163,184,0.08); }
.live-time { color: #64748b; flex-shrink: 0; width: 70px; }
.live-msg { color: #cbd5e1; flex: 1; }"""
assert s.count(old5) == 1, 'block5'
s = s.replace(old5, new5)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('live console patched')
