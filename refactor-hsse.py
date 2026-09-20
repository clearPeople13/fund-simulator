import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) import useSSE
old_import = "import { ref, onMounted, computed } from 'vue'"
new_import = "import { ref, onMounted, computed } from 'vue'\nimport { useSSE } from '../composables/useSSE'"
assert s.count(old_import) == 1
s = s.replace(old_import, new_import)

# 2) 删掉内联 liveLogs/liveStatus 定义，改用 useSSE
old_refs = """const liveLogs = ref<any[]>([]) // AI 实时日志流
const liveStatus = ref<'connecting'|'live'|'closed'>('connecting')"""
new_refs = "const { logs: liveLogs, status: liveStatus, connect: connectSSE } = useSSE('/api/ai/stream') // AI 实时日志流（SSE 复用 composable）"
assert s.count(old_refs) == 1
s = s.replace(old_refs, new_refs)

# 3) 删掉 startLiveStream 函数体，onMounted 改调 connectSSE
old_fn = """// AI 实时日志流（SSE）
const startLiveStream = () => {
  try {
    const es = new EventSource('/api/ai/stream')
    es.onopen = () => { liveStatus.value = 'live' }
    es.onerror = () => { liveStatus.value = 'closed' }
    es.onmessage = (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data)
        liveLogs.value.unshift(data)
        if (liveLogs.value.length > 60) liveLogs.value.length = 60
      } catch (e) { /* ignore */ }
    }
  } catch (e) { liveStatus.value = 'closed' }
}

onMounted(() => {
  loadAllData()
  startLiveStream()
})"""
new_fn = """onMounted(() => {
  loadAllData()
  connectSSE()
})"""
assert s.count(old_fn) == 1
s = s.replace(old_fn, new_fn)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('Home.vue useSSE refactored')
