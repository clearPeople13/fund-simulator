# -*- coding: utf-8 -*-
"""一次性改造：
1) engine/order-engine.js —— 本地日期 + 非交易时段禁止下单（硬校验）
2) frontend Alerts.vue / Reports.vue —— created_at(UTC) 转本地显示
"""
import io, re, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"

def read(p):
    with io.open(p, 'r', encoding='utf-8') as f:
        return f.read()

def write(p, s):
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)
    print('written:', p)

# ---------------- 1. order-engine.js ----------------
p = os.path.join(BASE, 'engine', 'order-engine.js')
s = read(p)

old_head = """async function createOrder(ctx, o) {
  const { db, audit } = ctx;
  const { userId, fundCode, orderType, amount, price, reason } = o;
  const today = new Date().toISOString().slice(0, 10);

  const fees = await feeModule.getFundFees(db, fundCode);"""

new_head = """// 本地日期 YYYY-MM-DD（交易日期以本地时区为准，避免 UTC 日期偏移）
function getLocalDateStr(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return y + '-' + m + '-' + day;
}

// 是否处于交易时段：本地周一~周五 09:00:00 ~ 15:05:59 允许下单
// （15:00 整后提交按 T+1 净值确认，属真实基金规则；15:05 尾差为收盘分析容错）
function isTradingWindow(now) {
  const dow = now.getDay();
  if (dow === 0 || dow === 6) return false;
  const t = now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds();
  return t >= 9 * 3600 && t <= 15 * 3600 + 5 * 60 + 59;
}

async function createOrder(ctx, o) {
  const { db, audit } = ctx;
  const { userId, fundCode, orderType, amount, price, reason } = o;
  const nowD = new Date();

  // 硬校验：AI/任何来源都只能在交易时段创建订单，杜绝盘外交易
  if (!isTradingWindow(nowD)) {
    throw new Error('非交易时段禁止下单（仅本地工作日 09:00-15:05 可下单）');
  }

  const today = getLocalDateStr(nowD);

  const fees = await feeModule.getFundFees(db, fundCode);"""

assert s.count(old_head) == 1, 'head block not found'
s = s.replace(old_head, new_head)

old_cut = """  // 真实基金规则：15:00 前（含盘中）下单按当日净值确认（T 日）；15:00 后下单按下一交易日净值确认（T+1 日）
  const nowD = new Date();
  const h = nowD.getHours(), m = nowD.getMinutes();
  const afterCutoff = (h > 15) || (h === 15 && m >= 0);
  let tradeDate = today;
  if (afterCutoff) {
    const nxt = new Date(nowD);
    nxt.setDate(nxt.getDate() + 1);
    tradeDate = nxt.getFullYear() + '-' + String(nxt.getMonth() + 1).padStart(2, '0') + '-' + String(nxt.getDate()).padStart(2, '0');
  }"""

new_cut = """  // 真实基金规则：15:00 前（含盘中）下单按当日净值确认（T 日）；15:00 后下单按下一交易日净值确认（T+1 日）
  const h = nowD.getHours(), m = nowD.getMinutes();
  const afterCutoff = (h > 15) || (h === 15 && m >= 0);
  let tradeDate = today;
  if (afterCutoff) {
    const nxt = new Date(nowD);
    nxt.setDate(nxt.getDate() + 1);
    tradeDate = getLocalDateStr(nxt);
  }"""

assert s.count(old_cut) == 1, 'cutoff block not found'
s = s.replace(old_cut, new_cut)

old_cancel = """  return new Promise((resolve, reject) => {
    const today = new Date().toISOString().slice(0, 10);
    db.run("UPDATE orders SET status='CANCELLED' WHERE id=? AND user_id=? AND status='SUBMITTED' AND order_date=?","""

new_cancel = """  return new Promise((resolve, reject) => {
    const today = getLocalDateStr(new Date());
    db.run("UPDATE orders SET status='CANCELLED' WHERE id=? AND user_id=? AND status='SUBMITTED' AND order_date=?","""

assert s.count(old_cancel) == 1, 'cancel block not found'
s = s.replace(old_cancel, new_cancel)

write(p, s)

# ---------------- 2. Alerts.vue ----------------
p = os.path.join(BASE, 'frontend', 'src', 'views', 'Alerts.vue')
s = read(p)

old_fn = """const loadAlerts = async () => {"""
new_fn = """// SQLite 存 UTC（无时区标记），按 UTC 解析转本地显示
const formatTime = (str: string | null | undefined): string => {
  if (!str) return '--'
  try {
    const d = new Date(/^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}/.test(str) && !/[zZ]|[+-]\\d{2}:\\d{2}$/.test(str) ? str.replace(' ', 'T') + 'Z' : str.replace(' ', 'T'))
    if (isNaN(d.getTime())) return str
    return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
  } catch {
    return str
  }
}

const loadAlerts = async () => {"""
assert s.count(old_fn) == 1, 'alerts fn anchor not found'
s = s.replace(old_fn, new_fn)

old_col1 = """          { title: '时间', dataIndex: 'created_at', width: 170 },
          { title: '事件类型', dataIndex: 'event_type', width: 170 },"""
new_col1 = """          { title: '时间', dataIndex: 'created_at', width: 170 },
          { title: '事件类型', dataIndex: 'event_type', width: 170 },"""
assert s.count(old_col1) == 1
# 给两张表加 bodyCell 渲染 created_at
old_tpl = """        <template #bodyCell=\"{ column, record }\">
          <template v-if=\"column.dataIndex === 'event_type'\">"""
new_tpl = """        <template #bodyCell=\"{ column, record }\">
          <template v-if=\"column.dataIndex === 'created_at'\">{{ formatTime(record.created_at) }}</template>
          <template v-else-if=\"column.dataIndex === 'event_type'\">"""
assert s.count(old_tpl) == 1, 'alerts bodyCell anchor not found'
s = s.replace(old_tpl, new_tpl)

old_tpl2 = """        <template #bodyCell=\"{ column, record }\">
          <template v-if=\"column.dataIndex === 'issue_type'\">"""
new_tpl2 = """        <template #bodyCell=\"{ column, record }\">
          <template v-if=\"column.dataIndex === 'created_at'\">{{ formatTime(record.created_at) }}</template>
          <template v-else-if=\"column.dataIndex === 'issue_type'\">"""
assert s.count(old_tpl2) == 1, 'alerts bodyCell2 anchor not found'
s = s.replace(old_tpl2, new_tpl2)

write(p, s)

# ---------------- 3. Reports.vue ----------------
p = os.path.join(BASE, 'frontend', 'src', 'views', 'Reports.vue')
s = read(p)

old_fn = """const loadReports = async () => {"""
new_fn = """// SQLite 存 UTC（无时区标记），按 UTC 解析转本地显示
const formatTime = (str: string | null | undefined): string => {
  if (!str) return '--'
  try {
    const d = new Date(/^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}/.test(str) && !/[zZ]|[+-]\\d{2}:\\d{2}$/.test(str) ? str.replace(' ', 'T') + 'Z' : str.replace(' ', 'T'))
    if (isNaN(d.getTime())) return str
    return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
  } catch {
    return str
  }
}

const loadReports = async () => {"""
assert s.count(old_fn) == 1, 'reports fn anchor not found'
s = s.replace(old_fn, new_fn)

old_disp = """          <div class=\"report-item-time\">{{ r.created_at }}</div>"""
new_disp = """          <div class=\"report-item-time\">{{ formatTime(r.created_at) }}</div>"""
assert s.count(old_disp) == 1, 'reports disp anchor not found'
s = s.replace(old_disp, new_disp)

write(p, s)

print('ALL OK')
