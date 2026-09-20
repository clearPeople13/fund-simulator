/**
 * useSSE：EventSource 封装（可复用）
 * 用法：const { logs, status, connect } = useSSE('/api/ai/stream')
 */
import { ref, onUnmounted } from 'vue'

export function useSSE(url: string, maxLogs = 60) {
  const logs = ref<any[]>([])
  const status = ref<'connecting' | 'live' | 'closed'>('connecting')
  let es: EventSource | null = null

  const connect = () => {
    try {
      es = new EventSource(url)
      es.onopen = () => { status.value = 'live' }
      es.onerror = () => { status.value = 'closed' }
      es.onmessage = (ev: MessageEvent) => {
        try {
          const data = JSON.parse(ev.data)
          logs.value.unshift(data)
          if (logs.value.length > maxLogs) logs.value.length = maxLogs
        } catch (e) { /* ignore */ }
      }
    } catch (e) { status.value = 'closed' }
  }

  onUnmounted(() => { if (es) es.close() })

  return { logs, status, connect }
}
