/**
 * AI自动操盘系统 - 入口文件
 * 使用 Vue 3.6 混合模式（Vapor + 虚拟DOM）
 * UI 库：Ant Design Vue v4
 */

import { createApp, vaporInteropPlugin } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import router from './router'
import App from './App.vue'
import './style.css'

// 创建应用（使用 createApp，支持虚拟DOM组件）
const app = createApp(App)

// 安装插件
app.use(createPinia())
app.use(router)
app.use(Antd)

// 安装 Vapor 互操作插件（支持 Vapor 组件）
app.use(vaporInteropPlugin)

// 挂载应用
app.mount('#app')

console.log('🚀 AI自动操盘系统已启动')
