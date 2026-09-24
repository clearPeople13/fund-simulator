<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { theme } from 'ant-design-vue'
import {
  LineChartOutlined,
  HomeOutlined,
  UnorderedListOutlined,
  BarChartOutlined,
  DownOutlined,
  BellOutlined,
  FileTextOutlined,
  UserOutlined
} from '@ant-design/icons-vue'
import axios from 'axios'

const router = useRouter()
const route = useRoute()

// 全局分析模式：rule（规则引擎）| ai（MIMO Pro 2.5）
const analysisMode = ref<'rule' | 'ai'>('ai')  // 默认走 AI

// 导航菜单高亮跟随当前路由（切换用户刷新后仍保持正确对应）
const activeIndex = computed(() => {
  const p = route.path
  if (p.startsWith('/funds')) return '/funds'
  if (p.startsWith('/market')) return '/market'
  if (p.startsWith('/analysis') || p.startsWith('/ai-analysis')) return '/analysis'
  if (p.startsWith('/alerts')) return '/alerts'
  if (p.startsWith('/reports')) return '/reports'
  if (p.startsWith('/profile')) return '/profile'
  return '/'
})

const selectedKeys = computed(() => [activeIndex.value])

// 用户相关
interface User {
  id: string
  name: string
  avatar: string
  style: string
  description: string
}

const users = ref<User[]>([])
const currentUser = ref<User>({
  id: 'default',
  name: '默认用户',
  avatar: '👤',
  style: '稳健型',
  description: ''
})

const handleSelect = ({ key }: { key: string }) => {
  router.push(key)
}

const handleUserMenuClick = ({ key }: { key: string }) => {
  switchUser(key)
}

// 加载用户列表
const loadUsers = async () => {
  try {
    const res = await axios.get('/api/users')
    users.value = res.data

    // 获取当前用户
    const currentRes = await axios.get('/api/users/current')
    currentUser.value = currentRes.data
  } catch (error) {
    console.error('加载用户失败:', error)
  }
}

// 切换用户
const switchUser = async (userId: string) => {
  try {
    await axios.post('/api/users/switch', { user_id: userId })

    // 刷新页面数据
    window.location.reload()
  } catch (error) {
    console.error('切换用户失败:', error)
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<template>
  <a-config-provider
    :theme="{
      algorithm: theme.darkAlgorithm,
      token: {
        colorPrimary: '#6366f1',
        colorBgContainer: '#1c2348',
        colorBgLayout: '#131a35',
        colorText: '#e8ebff',
        colorTextSecondary: '#b7bce0',
        colorBorder: '#2e3768',
        borderRadius: 8
      }
    }"
  >
    <div class="app-container">
      <header class="app-header">
        <div class="header-content">
          <div class="logo">
            <div class="logo-mark">
              <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="6" y="18" width="4" height="8" rx="1" fill="#6366f1" opacity="0.6"/>
                <rect x="12" y="14" width="4" height="12" rx="1" fill="#8b5cf6" opacity="0.8"/>
                <rect x="18" y="10" width="4" height="16" rx="1" fill="#22d3ee"/>
                <path d="M8 12 L14 8 L20 10 L26 4" stroke="#e0e7ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                <circle cx="26" cy="4" r="2" fill="#22d3ee"/>
              </svg>
            </div>
            <span class="logo-text">AI自动操盘</span>
          </div>
          <a-menu
            v-model:selectedKeys="selectedKeys"
            mode="horizontal"
            class="header-menu"
            :overflowed-indicator="'更多'"
            @click="handleSelect"
          >
            <a-menu-item key="/">
              <HomeOutlined />
              <span>首页</span>
            </a-menu-item>
            <a-menu-item key="/funds">
              <UnorderedListOutlined />
              <span>基金</span>
            </a-menu-item>
            <a-menu-item key="/market">
              <LineChartOutlined />
              <span>行情</span>
            </a-menu-item>
            <a-menu-item key="/analysis">
              <BarChartOutlined />
              <span>分析</span>
            </a-menu-item>
            <a-menu-item key="/alerts">
              <BellOutlined />
              <span>预警</span>
            </a-menu-item>
            <a-menu-item key="/reports">
              <FileTextOutlined />
              <span>报告</span>
            </a-menu-item>
            <a-menu-item key="/profile">
              <UserOutlined />
              <span>经理</span>
            </a-menu-item>
          </a-menu>
          <div class="header-right">
            <!-- 全局模式切换：规则 / AI -->
            <div class="global-mode-switch" @click.stop>
              <button 
                class="global-mode-btn" 
                :class="{ active: analysisMode === 'rule' }"
                @click="analysisMode = 'rule'"
                title="规则引擎模式"
              >规则</button>
              <button 
                class="global-mode-btn ai" 
                :class="{ active: analysisMode === 'ai' }"
                @click="analysisMode = 'ai'"
                title="MIMO Pro 2.5 AI 模式"
              >🤖 AI</button>
            </div>
            <a-dropdown trigger="click">
              <div class="user-switcher">
                <span class="user-avatar">{{ currentUser.avatar }}</span>
                <div class="user-info">
                  <span class="user-name">{{ currentUser.name }}</span>
                  <span class="user-style">{{ currentUser.style }}</span>
                </div>
                <DownOutlined class="dropdown-arrow" />
              </div>
              <template #overlay>
                <a-menu @click="handleUserMenuClick">
                  <a-menu-item
                    v-for="user in users"
                    :key="user.id"
                    :class="{ 'is-active': user.id === currentUser.id }"
                  >
                    <span class="dropdown-avatar">{{ user.avatar }}</span>
                    <div class="dropdown-user-info">
                      <span class="dropdown-name">{{ user.name }}</span>
                      <span class="dropdown-style">{{ user.style }} - {{ user.description }}</span>
                    </div>
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </div>
        </div>
      </header>

      <main class="app-main">
        <router-view />
      </main>

      <footer class="app-footer">
        <div class="footer-content">
          <p>© 2024 AI自动操盘系统 - 由交易分析团队全自动运行</p>
          <p class="disclaimer">⚠️ 本系统仅供学习交流，AI操盘结果不构成任何投资建议，投资有风险</p>
        </div>
      </footer>
    </div>
  </a-config-provider>
</template>

<style>
/* 全局设计 token 见 style.css（深色金融科技设计系统） */

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background:
    radial-gradient(1200px 600px at 85% -10%, rgba(99, 102, 241, 0.16), transparent 60%),
    radial-gradient(1000px 500px at -10% 10%, rgba(139, 92, 246, 0.12), transparent 60%),
    var(--bg);
  color: var(--text);
  -webkit-font-smoothing: antialiased;
}

/* 滚动条美化 */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2c3466; border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: #4f46e5; }

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: linear-gradient(90deg, #131a35 0%, #1d2452 55%, #2a3370 100%);
  color: white;
  padding: 0 24px;
  box-shadow: 0 4px 24px rgba(99, 102, 241, 0.25);
  border-bottom: 1px solid rgba(129, 140, 248, 0.25);
  position: sticky;
  top: 0;
  z-index: 1000;
  overflow: visible;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1400px;
  margin: 0 auto;
  gap: 16px;
  padding: 12px 0;
  flex-wrap: nowrap;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  white-space: nowrap;
  flex-shrink: 0;
  margin-right: auto;
}

.logo-mark {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(34,211,238,0.15));
  border: 1px solid rgba(99,102,241,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-mark svg {
  width: 22px;
  height: 22px;
}

.logo-text {
  font-size: 17px;
  font-weight: 700;
  background: linear-gradient(135deg, #e0e7ff, #a5f3fc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 0.5px;
}

.logo .logo-icon {
  font-size: 24px;
  color: #a5b4fc;
}

.header-menu {
  background: transparent !important;
  border: none !important;
  flex: 1;
  margin-left: 20px;
  line-height: normal;
  min-width: 0;
  white-space: nowrap;
}

.header-menu .ant-menu-item {
  color: rgba(255, 255, 255, 0.85) !important;
  border-bottom: none !important;
  font-weight: 500;
  border-radius: 10px;
  margin: 0 4px;
  transition: background 0.2s, color 0.2s;
}

.header-menu .ant-menu-item:hover {
  color: white !important;
  background: rgba(255, 255, 255, 0.16) !important;
}

.header-menu .ant-menu-item-selected {
  color: white !important;
  background: rgba(255, 255, 255, 0.16) !important;
}

.header-menu .ant-menu-item::after {
  display: none !important;
}

.header-right {
  margin-left: auto;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 全局模式切换：规则 / AI */
.global-mode-switch {
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  padding: 4px;
}

.global-mode-btn {
  padding: 6px 16px;
  border: none;
  border-radius: 16px;
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.global-mode-btn:hover {
  color: #fff;
}

.global-mode-btn.active {
  background: #1890ff;
  color: #fff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
}

.global-mode-btn.ai.active {
  background: #722ed1;
  box-shadow: 0 2px 8px rgba(114, 46, 209, 0.3);
}

/* 用户切换器 */
.user-switcher {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.user-switcher:hover {
  background: rgba(255, 255, 255, 0.25);
}

.user-avatar {
  font-size: 24px;
}

.user-info {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: white;
}

.user-style {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.8);
}

.user-switcher .dropdown-arrow {
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
}

/* 下拉菜单样式 */
.dropdown-avatar {
  font-size: 28px;
}

.dropdown-user-info {
  display: flex;
  flex-direction: column;
}

.dropdown-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.dropdown-style {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.app-main {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
  flex: 1;
}

.app-footer {
  background: linear-gradient(135deg, #131a35 0%, #1a2145 60%, #202655 100%);
  color: var(--text-muted);
  text-align: center;
  padding: 22px 20px;
  height: auto;
  border-top: 1px solid rgba(129, 140, 248, 0.2);
}

.footer-content p {
  margin: 4px 0;
  font-size: 13px;
}

.disclaimer {
  color: var(--text-muted);
  font-size: 12px;
  opacity: 0.8;
}

@media (max-width: 768px) {
  .header-content {
    display: grid;
    grid-template-columns: 1fr auto;
    grid-template-rows: auto auto;
    gap: 8px;
    padding: 12px 0;
  }

  .logo {
    grid-column: 1;
    grid-row: 1;
    margin-right: 0;
  }

  .header-right {
    grid-column: 2;
    grid-row: 1;
    margin-left: 0;
    margin-top: 0;
  }

  .header-menu {
    grid-column: 1 / -1;
    grid-row: 2;
    margin-left: 0;
    margin-top: 0;
  }
}
</style>
