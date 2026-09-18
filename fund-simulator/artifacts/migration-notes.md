# Element Plus → Ant Design Vue v4 迁移说明

## 迁移概要

- **迁移时间**: 2026-09-18
- **项目**: fund-simulator/frontend (Vue 3.6 + Vite 8 + TS)
- **源 UI 库**: Element Plus 2.14 + @element-plus/icons-vue 2.3
- **目标 UI 库**: Ant Design Vue 4.2 + @ant-design/icons-vue
- **构建状态**: `npm run build` 成功，0 类型错误

---

## 组件映射清单

### 全局/入口层

| Element Plus | Ant Design Vue | 说明 |
|---|---|---|
| `app.use(ElementPlus, { locale: zhCn })` | `app.use(Antd)` | main.ts 中全局注册 |
| `import 'element-plus/dist/index.css'` | `import 'ant-design-vue/dist/reset.css'` | 样式入口 |
| 全局注册所有 Element 图标 | 按需从 `@ant-design/icons-vue` import | 不再全局注册 |
| `<el-container>` / `<el-main>` / `<el-footer>` | `<div>` / `<main>` / `<footer>` | 普通语义化标签 |
| `<el-header>` | `<header>` | 普通语义化标签 |
| `<a-config-provider>` | — | 新增，包裹 darkAlgorithm + 自定义 token |

### 布局与导航

| Element Plus | Ant Design Vue | 说明 |
|---|---|---|
| `<el-menu :default-active="..." mode="horizontal" @select="...">` | `<a-menu v-model:selectedKeys="..." mode="horizontal" @click="...">` | selectedKeys 需为 computed 数组 |
| `<el-menu-item index="/">` | `<a-menu-item key="/">` | index → key |
| `<el-dropdown trigger="click" @command="...">` | `<a-dropdown trigger="click">` | @command → @click on inner a-menu |
| `<template #dropdown>` | `<template #overlay>` | 插槽名变更 |
| `<el-dropdown-menu>` / `<el-dropdown-item>` | `<a-menu>` / `<a-menu-item>` | 内嵌在 #overlay 中 |
| `<el-row :gutter="20">` / `<el-col :xs="24" :md="16">` | `<a-row>` / `<a-col>` | API 基本兼容 |

### 基础组件

| Element Plus | Ant Design Vue | 差异说明 |
|---|---|---|
| `<el-button type="primary">` | `<a-button type="primary">` | props 兼容；`plain` → `ghost` |
| `<el-card shadow="never">` | `<a-card :bordered="false">` | shadow → bordered；`#header` 插槽 → `#title` |
| `<el-tag type="success/warning/danger">` | `<a-tag color="green/orange/red">` | type 值不同，改用 color prop |
| `<el-input clearable prefix-icon="Search">` | `<a-input allow-clear>` + `#prefix` 插槽 | clearable → allow-clear；prefix-icon 字符串 → 插槽 |
| `<el-select v-model="...">` / `<el-option>` | `<a-select v-model:value="...">` / `<a-select-option>` | v-model → v-model:value |
| `<el-input type="number">` | `<a-input type="number">` | 兼容 |

### 表格（最大改动）

| Element Plus | Ant Design Vue | 说明 |
|---|---|---|
| `<el-table :data="list" v-loading="loading" stripe>` | `<a-table :data-source="list" :loading="loading">` | data → data-source；v-loading → :loading |
| `<el-table-column prop="x" label="X" width="100" />` | `:columns="[{ dataIndex:'x', title:'X', width:100, key:'x' }]"` | 模板列 → 配置式数组 |
| `<template #default="{ row }">` | `<template #bodyCell="{ column, record }">` | 插槽名与参数名变更 |
| `:sort-by="..."` | 不支持前端排序（当前未使用排序功能） | — |
| `fixed="right"` | `fixed: 'right'` | 列配置中 |
| `row-key` | `row-key` | 兼容 |

### 反馈组件

| Element Plus | Ant Design Vue | 差异说明 |
|---|---|---|
| `ElMessage.success/error/warning('...')` | `message.success/error/warning('...')` | 从 'ant-design-vue' 导入 |
| `ElMessageBox.confirm({...})` | `Modal.confirm({...})` | 从 'ant-design-vue' 导入 |
| `<el-alert type="info" :title="...">` | `<a-alert type="info" :message="...">` | title → message |
| `<el-alert :description="...">` | `<a-alert :description="...">` | 兼容 |
| `<el-progress :percentage="50" :show-text="false" color="#6366f1">` | `<a-progress :percent="50" :show-info="false" stroke-color="#6366f1">` | percentage → percent；show-text → show-info；color → stroke-color |
| `<a-spin :spinning="loading">` 包裹内容 | 替代 v-loading 指令 | Element Plus 无对应指令 |
| `<a-empty>` | `<a-empty>` | 兼容 |

### 图标映射（@element-plus/icons-vue → @ant-design/icons-vue）

| Element Plus 图标 | Ant Design Vue 图标 | 使用位置 |
|---|---|---|
| TrendCharts | LineChartOutlined | App.vue, Portfolio.vue, Analysis.vue |
| HomeFilled | HomeOutlined | App.vue |
| List | UnorderedListOutlined | App.vue |
| DataAnalysis | BarChartOutlined | App.vue, AIAnalysis.vue |
| ArrowDown | DownOutlined | App.vue |
| ArrowLeft | LeftOutlined | FundDetail.vue |
| MagicStick | ThunderboltOutlined | FundDetail.vue, Analysis.vue |
| Wallet | WalletOutlined | Portfolio.vue, Analysis.vue |
| Coin | DollarOutlined | Portfolio.vue, Analysis.vue |
| Odometer | DashboardOutlined | Portfolio.vue, Analysis.vue |
| Bottom | ArrowDownOutlined | Analysis.vue |
| DataLine | LineOutlined | Analysis.vue |
| Histogram | BarChartOutlined | Analysis.vue |
| InfoFilled | InfoCircleFilled | Analysis.vue |
| CircleCheck | CheckCircleFilled | Analysis.vue |
| Warning | WarningFilled | Analysis.vue |
| Document | FileOutlined | AIAnalysis.vue |

### 分页

| Element Plus | Ant Design Vue | 说明 |
|---|---|---|
| `<el-pagination v-model:current-page="page" :page-size="20" :total="total" layout="prev, pager, next, total">` | `<a-pagination v-model:current="page" :page-size="20" :total="total" :show-total="(t) => '共 ' + t + ' 只'">` | current-page → current；layout 废弃，用 show-total |

---

## 深色主题配置

通过 `a-config-provider` 的 `:theme` prop 设置：

```js
{
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
}
```

`style.css` 中删除了全部 `.el-*` 覆盖规则，替换为 `.ant-*` 深色细节覆盖（表格斑马纹、分页深色按钮、输入框深色、下拉面板深色等）。

---

## 修改文件清单

| 文件 | 变更类型 |
|---|---|
| `src/main.ts` | 重写：移除 ElementPlus，改用 Antd 全局注册 |
| `src/App.vue` | 重写：a-config-provider 包裹、a-menu/a-dropdown 迁移、图标按需导入 |
| `src/style.css` | 重写：删除全部 .el-* 规则，替换为 .ant-* 深色覆盖 |
| `src/views/Home.vue` | 修改：ElMessage → message，v-loading → a-spin，修复浅色徽章样式 |
| `src/views/Funds.vue` | 重写：el-table → a-table 配置式，el-card/row/col/input/select/pagination/tag/button 迁移 |
| `src/views/FundDetail.vue` | 重写：el-table → a-table，el-card/row/col/tag 迁移，图标替换 |
| `src/views/Portfolio.vue` | 重写：el-table → a-table，el-card/row/col/tag 迁移，图标替换 |
| `src/views/Analysis.vue` | 重写：el-table → a-table，el-alert/progress/row/col 迁移，图标替换 |
| `src/views/AIAnalysis.vue` | 重写：el-card/tag/select/button/progress/alert 迁移，ElMessage → message |
| `src/views/NotFound.vue` | 修改：el-button → a-button，修复深色文字颜色 |
| `package.json` | 变更：移除 element-plus + @element-plus/icons-vue，新增 ant-design-vue + @ant-design/icons-vue |

---

## 剩余问题与注意事项

1. **Trading.vue 未迁移**：该文件未挂路由，按要求保持不动。它仍引用 element-plus 组件和 ElMessage，但不会被路由加载/打包。如果未来需要启用交易页面，需单独迁移。

2. **types/element-plus-locale.d.ts 残留**：该类型声明文件引用了 element-plus 类型，但由于 Trading.vue 未被路由引入且 vue-tsc 未报错，暂不影响构建。如后续需要清理可删除。

3. **npm install 需 --legacy-peer-deps**：Vue 3.6 RC 版本与 ant-design-vue 的 peer dependency 声明（`vue >= 3.2.0`）存在严格解析冲突，安装/卸载时需加 `--legacy-peer-deps`。

4. **v-loading 替代方案**：Element Plus 的 `v-loading` 指令在 Ant Design Vue 中无直接对应。已用 `<a-spin :spinning="loading">` 包裹页面内容替代；表格加载用 a-table 的 `:loading` prop。

5. **el-table 排序功能未迁移**：原 Funds.vue 中 el-table-column 有 `sortable` 和 `:sort-by` 属性，但实际未使用排序交互（前端分页），a-table 中暂未实现排序。如需排序可后续添加 `sorter` 列配置。

6. **图表代码未改动**：所有 ECharts 初始化逻辑（echarts.init、setOption、resize 监听）原样保留，仅外层 UI 容器从 el-card 改为 a-card。

7. **页面宽度恒定**：`.app-main` 保持 `width: 100%`，无 max-width 和 margin auto，避免切换路由时滚动条出现/消失导致的宽度跳动。各视图内部自行控制 max-width: 1400px 居中。
