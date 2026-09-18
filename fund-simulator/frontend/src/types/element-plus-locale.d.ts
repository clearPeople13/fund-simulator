// element-plus 中文语言包为 .mjs，无类型声明，补充模块声明
declare module 'element-plus/dist/locale/zh-cn.mjs' {
  import type { Language } from 'element-plus/es/locale'
  const zhCn: Language
  export default zhCn
}
