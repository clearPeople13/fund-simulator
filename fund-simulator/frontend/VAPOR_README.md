# AI自动操盘系统 - Vue 3.6 Vapor Mode

## 版本信息

- **Vue 版本**: 3.6.0-rc.5
- **Vapor Mode**: 已启用
- **状态**: RC 版本，功能完整

## Vapor Mode 介绍

Vapor Mode 是 Vue 3.6 引入的新编译模式，跳过虚拟DOM，直接操作真实DOM。

### 性能提升（基于 Vue&ViteConf 2026 官方数据）

| 指标 | 传统虚拟DOM | Vapor Mode | 提升 |
|------|------------|------------|------|
| 包体积 | 22.8 kB | 7.9 kB | **-65%** |
| 渲染速度 | 19ms | 0ms | **-97%** |
| 内存占用 | 100% | 58% | **-42%** |
| 10万组件挂载 | - | 100ms内 | **极致性能** |

### 核心优势

1. **更小的包体积**: 移除虚拟DOM运行时代码
2. **更快的渲染速度**: 编译时优化，直接DOM操作
3. **更低的内存占用**: 无需维护虚拟DOM树
4. **更好的性能**: 细粒度响应式更新

## 启用方式

### 1. 创建应用（main.ts）

```typescript
import { createVaporApp, vaporInteropPlugin } from 'vue'

// 使用 Vapor Mode 创建应用
const app = createVaporApp(App)

// 安装互操作插件（支持与虚拟DOM组件混用）
app.use(vaporInteropPlugin)
```

### 2. 配置 Vite（vite.config.ts）

```typescript
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [
    vue({
      vapor: true  // 启用 Vapor Mode
    })
  ]
})
```

### 3. 组件（无需额外配置）

全局启用 Vapor Mode 后，所有组件自动使用 Vapor Mode，**无需**在每个组件上添加 `vapor` 属性：

```vue
<script setup lang="ts">
// 自动使用 Vapor Mode（全局启用）
</script>
```

> **注意**: 只有在混合模式下（部分组件使用 Vapor），才需要在特定组件上添加 `vapor` 属性。

## 当前项目配置

### main.ts

```typescript
import { createVaporApp, vaporInteropPlugin } from 'vue'

const app = createVaporApp(App)
app.use(vaporInteropPlugin)
```

### vite.config.ts

```typescript
vue({
  vapor: true
})
```

### 组件

```vue
<script setup lang="ts" vapor>
// Vapor Mode 组件
</script>
```

## 与 Element Plus 兼容

Element Plus 使用虚拟DOM，通过 `vaporInteropPlugin` 实现兼容：

```typescript
import { createVaporApp, vaporInteropPlugin } from 'vue'
import ElementPlus from 'element-plus'

const app = createVaporApp(App)
app.use(ElementPlus)
app.use(vaporInteropPlugin)  // 启用互操作
```

## 支持的特性

### ✅ 支持

- `<script setup>` + Composition API
- `v-if` / `v-for` / `v-model`
- `ref` / `reactive` / `computed` / `watch`
- TypeScript
- 自定义指令（新语法）

### ❌ 不支持

- Options API（data, methods, computed 等）
- 手动 `setup()` 函数
- SSR / Nuxt 水合（开发中）
- `<Suspense>`（开发中）
- `v-memo`
- `$el` / `$props` / `$attrs` / `$slots`

## 自定义指令（新语法）

Vapor Mode 使用不同的自定义指令接口：

```typescript
const MyDirective = (el: Element, valueGetter: () => any) => {
  watchEffect(() => {
    el.textContent = valueGetter()
  })
  return () => console.log('cleanup')
}
```

## 注意事项

1. **Vue 版本**: 必须使用 Vue 3.6.0-rc.5+
2. **Composition API**: 所有组件必须使用 `<script setup>`
3. **第三方库**: 虚拟DOM库需要通过 `vaporInteropPlugin` 兼容
4. **浏览器兼容**: 最低支持 Chrome 79+

## 性能优化建议

### 1. 优先优化高频更新组件

- 数据仪表盘
- 实时行情显示
- 列表/表格组件

### 2. 使用混合模式

对于大型项目，推荐使用混合模式：

```typescript
import { createApp, vaporInteropPlugin } from 'vue'

createApp(App)
  .use(vaporInteropPlugin)
  .mount('#app')
```

然后在需要优化的组件中添加 `vapor` 属性。

## 参考资料

- [Vue 3.6 RC 发布说明](https://github.com/vuejs/core/releases)
- [Vapor Mode 官方文档](https://vuejs.org/)
- [Vue&ViteConf 2026](https://vueconf.org/)

---

**项目版本**: v1.0.0
**Vue 版本**: 3.6.0-rc.5
**更新时间**: 2026-09-16