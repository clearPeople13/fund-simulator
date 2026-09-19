/**
 * 统一 API 出口（所有 axios 调用只走这里）
 * - 实例统一 baseURL / 超时 / 错误拦截
 * - 各业务模块从这里 import，不直接用 axios
 */
import axios from 'axios'

const client = axios.create({
  baseURL: '/',
  timeout: 30000,
})

// 响应拦截：HTTP 错误统一提示
client.interceptors.response.use(
  (resp) => resp,
  (error) => {
    console.error('[API]', error.config?.url, error.message)
    return Promise.reject(error)
  }
)

/** 数字格式化 */
export const fmtMoney = (v) => (v == null ? '—' : '¥' + Number(v).toLocaleString('zh-CN', { maximumFractionDigits: 2 }))
export const fmtPct = (v) => (v == null ? '—' : (v >= 0 ? '+' : '') + Number(v).toFixed(2) + '%')
/** 相对时间：n 分钟前 / 昨天 HH:mm */
export const fmtTime = (iso) => {
  try {
    const d = new Date(iso)
    const diff = (Date.now() - d.getTime()) / 1000
    if (diff < 60) return '刚刚'
    if (diff < 3600) return Math.floor(diff / 60) + ' 分钟前'
    if (diff < 86400) return Math.floor(diff / 3600) + ' 小时前'
    return d.toLocaleString('zh-CN', { hour12: false })
  } catch { return iso }
}

export default client
