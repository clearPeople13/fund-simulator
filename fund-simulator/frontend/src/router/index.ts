/**
 * 路由配置
 * @module router
 */

import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

// #region 路由配置

/**
 * 路由配置列表
 */
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: { title: 'AI操盘' }
  },
  {
    path: '/funds',
    name: 'Funds',
    component: () => import('../views/Funds.vue'),
    meta: { title: '基金列表' }
  },
  {
    path: '/funds/:code',
    name: 'FundDetail',
    component: () => import('../views/FundDetail.vue'),
    meta: { title: '基金详情' }
  },
  {
    path: '/market',
    name: 'Market',
    component: () => import('../views/Market.vue'),
    meta: { title: '市场行情' }
  },
  {
    path: '/portfolio',
    name: 'Portfolio',
    component: () => import('../views/Portfolio.vue'),
    meta: { title: '我的组合' }
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: () => import('../views/Analysis.vue'),
    meta: { title: '分析' }
  },
  {
    path: '/ai-analysis',
    name: 'AIAnalysis',
    component: () => import('../views/AIAnalysis.vue'),
    meta: { title: 'AI智能分析' }
  },
  {
    path: '/alerts',
    name: 'Alerts',
    component: () => import('../views/Alerts.vue'),
    meta: { title: '预警中心' }
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('../views/Reports.vue'),
    meta: { title: '报告中心' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: { title: '基金经理画像' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue'),
    meta: { title: '页面未找到' }
  }
]

// #endregion

// #region 创建路由实例

/**
 * 路由实例
 */
const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// #endregion

// #region 路由守卫

/**
 * 全局前置守卫
 * 设置页面标题
 */
router.beforeEach((to, _from, next) => {
  const title = to.meta.title as string
  document.title = title ? `${title} - AI自动操盘系统` : 'AI自动操盘系统'
  next()
})

// #endregion

export default router