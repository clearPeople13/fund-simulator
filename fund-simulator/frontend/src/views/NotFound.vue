<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="not-found">
    <h1>404</h1>
    <p>页面未找到</p>
    <a-button type="primary" @click="router.push('/')">返回首页</a-button>
  </div>
</template>

<style scoped>
.not-found {
  text-align: center;
  padding: 100px 20px;
}
.not-found h1 {
  font-size: 6rem;
  color: #6366f1;
  margin-bottom: 20px;
}
.not-found p {
  font-size: 1.5rem;
  color: var(--text-secondary);
  margin-bottom: 30px;
}
</style>
