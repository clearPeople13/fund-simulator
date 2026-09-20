<template>
  <!-- 数字卡复用组件：标题+数值+涨跌色+图标+副文 -->
  <div class="stat-card" :class="tone">
    <div v-if="icon" class="stat-icon">{{ icon }}</div>
    <div class="stat-body">
      <div class="stat-label">{{ label }}</div>
      <div class="stat-value">{{ value }}</div>
      <div v-if="sub" class="stat-sub">{{ sub }}</div>
    </div>
  </div>
</template>

<script setup>
// 数字卡：tone = primary/success/danger/info/warning，由父组件按涨跌传
defineProps({
  label: { type: String, required: true },
  value: { type: String, required: true },
  icon: { type: String, default: '' },
  sub: { type: String, default: '' },
  tone: { type: String, default: 'primary' }
})
</script>

<style scoped>
.stat-card { display: flex; align-items: center; gap: 12px; padding: 16px; border-radius: 12px;
  background: rgba(15,23,42,0.6); border: 1px solid rgba(99,102,241,0.15); }
.stat-icon { font-size: 24px; }
.stat-label { font-size: 12px; color: #94a3b8; }
.stat-value { font-size: 20px; font-weight: 700; color: #e2e8f0; margin-top: 2px; }
.stat-sub { font-size: 11px; color: #64748b; margin-top: 2px; }
.tone-success .stat-value { color: var(--up); }
.tone-danger .stat-value { color: var(--down); }
</style>
