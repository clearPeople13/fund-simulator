# -*- coding: utf-8 -*-
"""恢复 Home.vue：script 块中 l→i 的系统性混淆反替换。
词典来源：dist 17:16 正常构建的 chunk（含正确英文标识符）。
规则：token 在词典中→不动；否则尝试把部分 i 还原为 l，取在词典中且最长的候选。
"""
import re, os, json

ROOT = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend"
SRC = os.path.join(ROOT, "src", "views", "Home.vue")
DIST = os.path.join(ROOT, "dist", "assets")

# 1. 构建词典：从 dist chunk 提取英文 token 词频
vocab = {}
for fn in os.listdir(DIST):
    if not fn.endswith(".js"):
        continue
    txt = open(os.path.join(DIST, fn), "r", encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r"[A-Za-z_$][A-Za-z0-9_$]{1,}", txt):
        w = m.group(0)
        vocab[w] = vocab.get(w, 0) + 1

# 补充 JS/TS 关键字与常用词（防词典缺词）
EXTRA = """const let var function return if else for while do switch case break continue default
typeof instanceof new delete void this null undefined true false import export from require
module exports async await yield class extends super static get set try catch finally throw
ref computed onMounted onBeforeUnmount watch nextTick defineComponent h createApp useRouter
useRoute useStore axios echarts router push replace query params path name value values
load all data list item items fund funds code user users status date time format string
number boolean array object record any string unknown never promise resolve reject error
console log info warn table debug error group groupEnd time timeEnd count assert dir
template style script setup lang ts js element plus message progress analysis analyze
normalize normal format local locale year month day hour minute second numeric digit
current total asset portfolio profit loss rate return yield amount position holding
watch watchlist manual ai signal buy sell add wait hold decision reason recommend
observe observed detail view navigate go back refresh status running stop paused
update create delete insert remove add save edit cancel confirm submit response
request fetch get post put delete patch json url api endpoint header token auth
login logout switch type text input select option button checkbox radio label
name title desc description icon search filter sort order asc desc page size limit
offset row column table card grid container main header footer section block panel
tab tabs item active hover disabled readonly required placeholder value model
change input click blur focus keyup keydown mouseenter mouseleave transition
animation keyframe display flex grid none block inline margin padding border
radius shadow color background font weight size line height width height min max
top bottom left right center middle start end space between around baseline
wrap nowrap hidden visible overflow auto scroll fixed absolute relative sticky
opacity transform translate scale rotate smooth cubic bezier ease linear infinite
singleton composition injection provide inject symbol version platform web mobile
desktop window document body html app head meta link script style class id attr
attribute properties prop props emit slots slot scoped deep vfor vif vshow vmodel
vbind von vonce vhtml vtext refs reactive toRef toRefs shallow readonly markRaw
isRef unref toRaw effect stop runner scheduler flush post sync pre async onBefore
onBeforeMount onMounted onUpdated onBeforeUnmount onUnmounted onActivated onDeactivated
onErrorCaptured onRenderTracked onRenderTriggered getCurrentInstance hFragment
createApp nextTick appConfig globalProperties warn error warnHandler errorHandler
app mount unmount container innerHTML outerHTML textContent innerText classList
querySelector querySelectorAll getElementById getElementsByClassName
getElementsByTagName addEventListener removeEventListener preventDefault
stopPropagation localStorage sessionStorage getItem setItem removeItem clear
JSON stringify parse length push pop shift unshift splice slice concat join
split indexOf lastIndexOf includes startsWith endsWith charAt charCodeAt
toUpperCase toLowerCase trim replace match search test exec compile source
flags global sticky multiline ignoreCase unicode dotAll date now getTime
setTime getFullYear getMonth getDate getDay getHours getMinutes getSeconds
getMilliseconds toLocaleString toISOString toUTCString setFullYear setMonth
setDate setHours setMinutes setSeconds setTimeout setInterval clearTimeout
clearInterval requestAnimationFrame cancelAnimationFrame Promise resolve
reject all race allSettled any finally then catch finally symbol iterator
asyncGenerator next throw done return value done generator yield delegate
""".split()
for w in EXTRA:
    vocab[w] = vocab.get(w, 0) + 100

def best_fix(tok):
    """对含 i 的 token，尝试 i→l 组合，返回词典中最优候选；无候选返回原 token。"""
    if tok in vocab:
        return tok
    idxs = [i for i, ch in enumerate(tok) if ch == "i"]
    if not idxs:
        return tok
    # 生成候选：最多替换 3 个 i（组合数控制）
    from itertools import combinations
    cands = {}
    for k in range(1, min(len(idxs), 3) + 1):
        for comb in combinations(idxs, k):
            lst = list(tok)
            for i in comb:
                lst[i] = "l"
            w = "".join(lst)
            if w in vocab:
                cands[w] = vocab[w]
    if not cands:
        return tok
    # 取词频最高；同频取最长
    best = max(cands.items(), key=lambda kv: (kv[1], len(kv[0])))
    return best[0]

raw = open(SRC, "r", encoding="utf-8").read()
backup = SRC + ".confused.bak"
open(backup, "w", encoding="utf-8").write(raw)
print("已备份混淆版到:", backup)

# 只处理 script 块
m = re.search(r"(<script[^>]*>)(.*?)(</script>)", raw, re.S)
assert m, "未找到 script 块"
script_body = m.group(2)

# token 化：只替换英文标识符（保留中文字符串与符号）
def repl(mo):
    tok = mo.group(0)
    fixed = best_fix(tok)
    return fixed

new_body = re.sub(r"[A-Za-z_$][A-Za-z0-9_$]*", repl, script_body)

# 统计差异
old_tokens = set(re.findall(r"[A-Za-z_$][A-Za-z0-9_$]*", script_body))
new_tokens = set(re.findall(r"[A-Za-z_$][A-Za-z0-9_$]*", new_body))
changed = old_tokens - new_tokens
print("修改的 token 数:", len(changed))
for t in sorted(changed)[:120]:
    print(" ", t)

out = raw[:m.start(2)] + new_body + raw[m.end(2):]
open(SRC, "w", encoding="utf-8").write(out)
print("已写回:", SRC)
