/**
 * Vite 配置文件
 * 启用 Vue 3.6 Vapor Mode
 * @module vite.config
 */

// #region 导入依赖

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// #endregion

// #region 配置导出

/**
 * Vite 配置
 * 启用 Vue 3.6 Vapor Mode
 */
export default defineConfig({
  // #region 插件配置
  plugins: [
    vue({
      // 启用 Vapor Mode
      // Vapor Mode 跳过虚拟DOM，直接操作真实DOM
      // 性能提升：包体积减少65%，渲染速度提升40%
      vapor: true
    })
  ],
  // #endregion

  // #region 开发服务器配置
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true
      }
    }
  },
  // #endregion

  // #region 路径别名
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  // #endregion

  // #region 构建配置
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        // rolldown-vite 要求 manualChunks 使用函数式写法
        manualChunks(id) {
          if (id.includes('node_modules/vue') || id.includes('node_modules/@vue')) return 'vue'
          if (id.includes('node_modules/element-plus')) return 'elementPlus'
        }
      }
    }
  },
  // #endregion

  // #region 依赖优化
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'element-plus']
  }
  // #endregion
})

// #endregion