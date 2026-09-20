# -*- coding: utf-8 -*-
"""Home.vue：资产总览上方加「AI 状态横幅」——今日盈亏大字 + AI 实时状态"""
import io

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """    <!-- 资产总览卡片 -->
    <div class="overview-cards">"""
new = """    <!-- AI 状态横幅：今日盈亏大字 + AI 当前动作（实时） -->
    <div class="ai-banner">
      <div class="ai-banner-left">
        <div class="ai-banner-label">今日盈亏</div>
        <div class="ai-banner-value" :class="todayPnl === null ? '' : (todayPnl >= 0 ? 'up' : 'down')">
          <template v-if="todayPnl === null">待更新</template>
          <template v-else>{{ todayPnl >= 0 ? '+' : '' }}¥{{ todayPnl.toFixed(2) }}</template>
        </div>
        <div class="ai-banner-sub">
          累计 <span :class="totalPnl >= 0 ? 'up' : 'down'">{{ totalPnl >= 0 ? '+' : '' }}¥{{ totalPnl.toFixed(2) }}</span>
          · 收益率 <span :class="parseFloat(totalPnlRate) >= 0 ? 'up' : 'down'">{{ totalPnlRate }}%</span>
        </div>
      </div>
      <div class="ai-banner-right">
        <span class="ai-banner-dot" :class="liveStatus === 'live' ? 'on' : 'off'"></span>
        <div class="ai-banner-ai">
          <div class="ai-banner-ai-label">AI 当前动作</div>
          <div class="ai-banner-ai-msg">{{ liveLogs[0] ? liveLogs[0].message : '等待 AI 下次分析（交易日盘中每 30 分钟）…' }}</div>
        </div>
      </div>
    </div>

    <!-- 资产总览卡片 -->
    <div class="overview-cards">"""
assert s.count(old) == 1, 'overview anchor'
s = s.replace(old, new)

# 样式
old_css = """.muted { color: #64748b; font-size: 12px; font-weight: 400; }"""
new_css = """.muted { color: #64748b; font-size: 12px; font-weight: 400; }
.ai-banner { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-radius: 14px;
  background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(15,23,42,0.6)); border: 1px solid rgba(99,102,241,0.25); margin-bottom: 16px; }
.ai-banner-label { font-size: 13px; color: #94a3b8; }
.ai-banner-value { font-size: 40px; font-weight: 800; line-height: 1.1; margin: 4px 0; }
.ai-banner-value.up { color: var(--up); }
.ai-banner-value.down { color: var(--down); }
.ai-banner-sub { font-size: 13px; color: #94a3b8; }
.ai-banner-sub .up { color: var(--up); font-weight: 600; }
.ai-banner-sub .down { color: var(--down); font-weight: 600; }
.ai-banner-right { display: flex; align-items: center; gap: 10px; max-width: 420px; }
.ai-banner-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.ai-banner-dot.on { background: var(--up); box-shadow: 0 0 8px var(--up); animation: pulse 2s infinite; }
.ai-banner-dot.off { background: #64748b; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
.ai-banner-ai-label { font-size: 11px; color: #64748b; }
.ai-banner-ai-msg { font-size: 13px; color: #cbd5e1; margin-top: 2px; }"""
assert s.count(old_css) == 1, 'css anchor'
s = s.replace(old_css, new_css)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('AI banner patched')
