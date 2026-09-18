# -*- coding: utf-8 -*-
"""全文反混淆：Home.vue 的 l→i 混淆（script/template/style 全覆盖）。
词典：dist chunks + 当前 script 已恢复标识符 + 内置 CSS/Vue/HTML/EP 词表。
"""
import re, os
from itertools import combinations

ROOT = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend"
SRC = os.path.join(ROOT, "src", "views", "Home.vue")
DIST = os.path.join(ROOT, "dist", "assets")

vocab = {}
for fn in os.listdir(DIST):
    if fn.endswith(".js"):
        txt = open(os.path.join(DIST, fn), "r", encoding="utf-8", errors="ignore").read()
        for m in re.finditer(r"[A-Za-z_$][A-Za-z0-9_$]{1,}", txt):
            w = m.group(0)
            vocab[w] = vocab.get(w, 0) + 1

# 当前文件 script 中已恢复的标识符也入词典（覆盖自定义名）
raw_now = open(SRC, "r", encoding="utf-8").read()
m = re.search(r"(<script[^>]*>)(.*?)(</script>)", raw_now, re.S)
if m:
    for t in re.findall(r"[A-Za-z_$][A-Za-z0-9_$]{2,}", m.group(2)):
        vocab[t] = vocab.get(t, 0) + 50

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
align justify items content space around between baseline stretch shrink grow basis
auto flex wrap nowrap column row reverse start end center flexstart flexend
spacebetween spacearound spaceevenly display inlineblock inlineflex grid
gridtemplate gridtemplaterows gridtemplatecolumns gridtemplateareas gridgap
gridrow gridcolumn gridarea justifyself alignself aligncontent order zindex
visibility content cursor pointer notallowed textalign textdecoration
texttransform uppercase lowercase capitalize textindent textoverflow ellipsis
clip whitespace nowrap pre prewrap preline wordbreak breakall keepall
wordwrap breakword verticalalign sub super texttop textbottom middle baseline
bordercollapse borderspacing emptyshow borderless outline outlinewidth
outlinestyle outlinestolor outlineoffset boxshadow inset outset
backgroundattachment backgroundclip backgroundorigin backgroundposition
backgroundrepeat norepeat repeatx repeaty cover contain
backgroundsize backgroundimage backgroundcolor lineheight letterspacing
fontfamily sansserif serif monospace sans fontstyle italic normal oblique
fontweight bold bolder lighter fontvariant smallcaps fontstretch fontsizeadjust
color rgba hsla opacity filter blur brightness contrast grayscale saturate
huerotate invert sepia drop shadow transitionproperty transitionduration
transitiontimingfunction transitiondelay animationname animationduration
animationtimingfunction animationdelay animationiterationcount animationdirection
animationfillmode animationplaystate keyframes from to percent vw vh vmin vmax
em rem px pt pc cm mm in ex ch table thead tbody tfoot tr td th caption
colspan rowspan scope abbr axis valign cellspacing cellpadding bgcolor
clearfix ellipsis nowrap href src alt target rel charset method action enctype
accept download datetime autofocus autocomplete minlength maxlength pattern
title lang content type submit reset button textarea fieldset legend label
img svg canvas audio video source track picture figure figcaption article
section aside nav main header footer h1 h2 h3 h4 h5 h6 p span strong em b i u
small big code pre kbd samp var del ins mark q blockquote cite abbr address
time progress meter details summary dialog menu menuitem datalist optgroup
option output select input checkbox radio range color date datetime
datetimelocal email file hidden image month number password tel time url week
form formaction formenctype formmethod formnovalidate formtarget novalidate
readonly selected checked multiple disabled required placeholder value name id
elcontainer elheader elmain elfooter elcard elbutton elinput elselect eloption
eltable eltablecolumn eltag elalert elprogress elpagination eltabs eltabpane
eldialog elform elformitem elicon elmenu elmenuitem eldropdown eldropdownmenu
eldropdownitem eltooltip elpopover elbadge elavatar elradio elcheckbox elswitch
elslider eldatepicker eltimepicker elupload elrate elsteps elstep
elbreadcrumb elbreadcrumbitem elpageheader elelment elempty elskeleton
elcarousel elcarouselitem elcollapse elcollapseitem eltimeline eltimelineitem
eldivider elimage ellink elstatistic elcountdown elcalendar eldescriptions
eldescriptionsitem elresult elaffix elbacktop eldrawer eltree elselectv2
eltreeselect elcascader elcolorpicker elinputnumber elmention eloverlay
elscrollbar elwatermark elconfigprovider elspace dynamic vfor vif vshow vmodel
vbind von vonce vpre vcloak vhtml vtext vslot slot slotscope key
days today weekly monthly quarterly yearly cumulative simple compound
gross net pre post ex before after during since until between among with
without through across around inside outside above below over under up down
out in off on at by for from to of and or nor not but yet so
pnl nav asset cap gain earn income expense fee tax trade exchange clearing
settlement cash balance ledger book record history daily weekly monthly
signal grade score ranking percentile quantile decile quartile median mean
avg stdev deviation variance skew kurtosis corr covariance weight rebalance
allocation exposure concentration diversification drift target stop threshold
limit order execution fill slippage latency throughput benchmark relative
absolute excess riskfree sharpe sortino calmar maxdrawdown downside upside
capture return volatility beta alpha information treynor jensen modigliani
""".split()
for w in EXTRA:
    vocab[w] = vocab.get(w, 0) + 100

def best_fix(tok):
    if tok in vocab:
        return tok
    idxs = [i for i, ch in enumerate(tok) if ch == "i"]
    if not idxs:
        return tok
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
    best = max(cands.items(), key=lambda kv: (kv[1], len(kv[0])))
    return best[0]

raw = open(SRC, "r", encoding="utf-8").read()
open(SRC + ".confused2.bak", "w", encoding="utf-8").write(raw)
print("已备份当前状态 ->", SRC + ".confused2.bak")

def repl(mo):
    return best_fix(mo.group(0))

new = re.sub(r"[A-Za-z_$][A-Za-z0-9_$]*", repl, raw)

old_tok = set(re.findall(r"[A-Za-z_$][A-Za-z0-9_$]*", raw))
new_tok = set(re.findall(r"[A-Za-z_$][A-Za-z0-9_$]*", new))
changed = old_tok - new_tok
print("修改 token 数:", len(changed))
for t in sorted(changed):
    print(" ", t)

open(SRC, "w", encoding="utf-8").write(new)
print("已写回:", SRC)
