<template>
  <!-- 空状态复用组件：图标+提示文+可选操作按钮 -->
  <div class="empty-state">
    <div class="empty-icon">{{ icon || '📭' }}</div>
    <div class="empty-title">{{ title || '暂无数据' }}</div>
    <div v-if="desc" class="empty-desc">{{ desc }}</div>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  icon: { type: String, default: '' },
  title: { type: String, default: '' },
  desc: { type: String, default: '' }
})
</script>

<style scoped>
.empty-state { text-align: center; padding: 40px 20px; color: #64748b; }
.empty-icon { font-size: 40px; margin-bottom: 12px; }
.empty-title { font-size: 15px; color: #94a3b8; font-weight: 500; }
.empty-desc { font-size: 13px; margin-top: 6px; color: #64748b; }
</style>
