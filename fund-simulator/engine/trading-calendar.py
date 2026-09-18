# -*- coding: utf-8 -*-
"""法定节假日交易日历：
1) engine/holidays.json 已建（2026 年 A 股休市日，国办发明电〔2025〕7号）
2) order-engine.js：isTradingWindow 加 isTradingDay（工作日 && 非节假日）硬校验
3) server.js：scheduleCloseAnalysis/schedulePreCloseAnalysis 顺延到下一交易日；
   scheduleRealtimeAnalysis 非交易日不启动盘中分析；initDatabase 建 holidays 表并 seed
"""
import io, os, json

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"

with io.open(os.path.join(BASE, 'engine', 'holidays.json'), 'r', encoding='utf-8') as f:
    HOLIDAYS = json.load(f)

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

old = """// 本地日期 YYYY-MM-DD（交易日期以本地时区为准，避免 UTC 日期偏移）
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
}"""

new = """// 本地日期 YYYY-MM-DD（交易日期以本地时区为准，避免 UTC 日期偏移）
function getLocalDateStr(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return y + '-' + m + '-' + day;
}

// A股休市日（工作日内的法定节假日，来源：engine/holidays.json，国务院办公厅 2026 年节假日通知）
let holidaySet = null;
function loadHolidays() {
  if (holidaySet) return;
  holidaySet = new Set();
  try {
    const h = require('./holidays.json');
    const year = String(new Date().getFullYear());
    (h[year] || []).forEach(d => holidaySet.add(d));
  } catch (e) {
    holidaySet = new Set();
  }
}

// 是否交易日：周一~周五 且 非节假日
function isTradingDay(now) {
  loadHolidays();
  const dow = now.getDay();
  if (dow === 0 || dow === 6) return false;
  return !holidaySet.has(getLocalDateStr(now));
}

// 是否处于交易时段：本地交易日 09:00:00 ~ 15:05:59 允许下单
// （15:00 整后提交按 T+1 净值确认，属真实基金规则；15:05 尾差为收盘分析容错）
function isTradingWindow(now) {
  if (!isTradingDay(now)) return false;
  const t = now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds();
  return t >= 9 * 3600 && t <= 15 * 3600 + 5 * 60 + 59;
}"""

assert s.count(old) == 1, 'order-engine window block not found'
s = s.replace(old, new)
write(p, s)

# ---------------- 2. server.js ----------------
p = os.path.join(BASE, 'server.js')
s = read(p)

# 2.1 require holidays + isTradingDay 辅助（放在 getLocalDateStr 后）
anchor = """function getLocalDateStr(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}"""
add = anchor + """

// A股休市日（工作日内的法定节假日）：engine/holidays.json（国办发明电〔2025〕7号，2026）
const HOLIDAYS = (() => {
  try {
    return require('./engine/holidays.json');
  } catch {
    return {};
  }
})();

// 是否交易日：周一~周五 且 非节假日（节假日每年 11 月国务院公布后补充 holidays.json）
function isTradingDay(d = new Date()) {
  const dow = d.getDay();
  if (dow === 0 || dow === 6) return false;
  const year = String(d.getFullYear());
  const list = HOLIDAYS[year] || [];
  return list.indexOf(getLocalDateStr(d)) === -1;
}

// 找到不小于 date 的第一个交易日 0 点
function nextTradingDay(date) {
  const d = new Date(date);
  while (!isTradingDay(d)) {
    d.setDate(d.getDate() + 1);
  }
  return d;
}"""
assert s.count(anchor) == 1, 'server localdate anchor not found'
s = s.replace(anchor, add)

# 2.2 initDatabase 建 holidays 表 + seed（在 CREATE TABLE 区找一个锚点）
seed_anchor = """      watchlist_source TEXT DEFAULT 'manual',"""
# 先看是否存在该锚点，不存在则用其他锚点
if s.count(seed_anchor) == 0:
    # 尝试 watchlist 表定义附近
    seed_anchor = None

# 直接在 getLocalDateStr 之前的合适位置插入建表逻辑不现实；改为在 initDatabase 里现有 watchlist 建表后追加。
# 找到 "CREATE TABLE IF NOT EXISTS watchlist" 段落结尾
wl_anchor = """    db.run(`CREATE TABLE IF NOT EXISTS watchlist ("""
if s.count(wl_anchor) != 1:
    raise SystemExit('watchlist table anchor not found')
# 在其后插入 holidays 建表 + seed（在 initDatabase 的 db.run 链中追加）
holidays_tbl = """    db.run(`CREATE TABLE IF NOT EXISTS watchlist ("""
# 查找 watchlist 建表语句完整块
import re
m = re.search(r"db\.run\(`CREATE TABLE IF NOT EXISTS watchlist \([^`]*?`\);", s)
if not m:
    raise SystemExit('watchlist create block regex not found')
wl_block = m.group(0)
holidays_block = wl_block + """

    db.run(`CREATE TABLE IF NOT EXISTS holidays (
      date TEXT PRIMARY KEY,
      name TEXT
    )`);
    // seed 2026 年休市日（幂等）
    const hd = (require('./engine/holidays.json')['2026'] || []);
    const hStmt = db.prepare('INSERT OR IGNORE INTO holidays (date, name) VALUES (?, ?)');
    hd.forEach(d => hStmt.run(d, '法定节假日休市'));
    hStmt.finalize();"""
assert s.count(wl_block) == 1, 'watchlist block count != 1'
s = s.replace(wl_block, holidays_block)

# 2.3 scheduleCloseAnalysis 顺延到下一交易日
old_close = """  if (now > targetTime) {
    targetTime.setDate(targetTime.getDate() + 1);
  }
  
  const delay = targetTime.getTime() - now.getTime();
  console.log(`[收盘分析] 下次分析: ${targetTime.toLocaleString('zh-CN')}`);
  
  setTimeout(() => {
    performAnalysis('close', true);
    // 每天执行一次
    setInterval(() => performAnalysis('close', true), 24 * 60 * 60 * 1000);
  }, delay);"""
new_close = """  if (now > targetTime) {
    targetTime.setDate(targetTime.getDate() + 1);
  }
  // 非交易日顺延到下一交易日
  if (!isTradingDay(targetTime)) {
    targetTime = nextTradingDay(targetTime);
    targetTime.setHours(15, 0, 0, 0);
  }
  
  const delay = targetTime.getTime() - now.getTime();
  console.log(`[收盘分析] 下次分析: ${targetTime.toLocaleString('zh-CN')}`);
  
  setTimeout(() => {
    performAnalysis('close', true);
    // 每个交易日执行一次
    setInterval(() => performAnalysis('close', true), 24 * 60 * 60 * 1000);
  }, delay);"""
assert s.count(old_close) == 1, 'close schedule block not found'
s = s.replace(old_close, new_close)

# 2.4 schedulePreCloseAnalysis 顺延
old_pre = """  if (now > targetTime) {
    targetTime.setDate(targetTime.getDate() + 1);
  }
  
  const delay = targetTime.getTime() - now.getTime();
  console.log(`[收盘前分析] 下次分析: ${targetTime.toLocaleString('zh-CN')}`);
  
  setTimeout(() => {
    performAnalysis('pre_close', true);
    // 每天执行一次
    setInterval(() => performAnalysis('pre_close', true), 24 * 60 * 60 * 1000);
  }, delay);"""
new_pre = """  if (now > targetTime) {
    targetTime.setDate(targetTime.getDate() + 1);
  }
  // 非交易日顺延到下一交易日
  if (!isTradingDay(targetTime)) {
    targetTime = nextTradingDay(targetTime);
    targetTime.setHours(14, 30, 0, 0);
  }
  
  const delay = targetTime.getTime() - now.getTime();
  console.log(`[收盘前分析] 下次分析: ${targetTime.toLocaleString('zh-CN')}`);
  
  setTimeout(() => {
    performAnalysis('pre_close', true);
    // 每个交易日执行一次
    setInterval(() => performAnalysis('pre_close', true), 24 * 60 * 60 * 1000);
  }, delay);"""
assert s.count(old_pre) == 1, 'pre_close schedule block not found'
s = s.replace(old_pre, new_pre)

# 2.5 scheduleRealtimeAnalysis：交易时段 + 交易日双条件
old_rt = """  // 交易时间: 9:30-11:30, 13:00-15:00
  const isTradingHour = (hour >= 9 && hour < 12) || (hour >= 13 && hour < 15);
  
  if (isTradingHour) {"""
new_rt = """  // 交易时间: 9:30-11:30, 13:00-15:00（且必须为交易日）
  const isTradingHour = (hour >= 9 && hour < 12) || (hour >= 13 && hour < 15);
  
  if (isTradingHour && isTradingDay(now)) {"""
assert s.count(old_rt) == 1, 'realtime trading hour block not found'
s = s.replace(old_rt, new_rt)

# 2.6 realtime 非交易时段分支：跳节假日（nextTradingTime 用 nextTradingDay）
old_rt2 = """    if (hour < 9 || (hour === 9 && minute < 30)) {
      nextTradingTime.setHours(9, 30, 0, 0);
    } else if (hour >= 15) {
      nextTradingTime.setDate(nextTradingTime.getDate() + 1);
      nextTradingTime.setHours(9, 30, 0, 0);
    } else if (hour >= 12) {
      nextTradingTime.setHours(13, 0, 0, 0);
    }
    
    const delay = nextTradingTime.getTime() - now.getTime();
    console.log(`[实时分析] 非交易时间，下次分析: ${nextTradingTime.toLocaleString('zh-CN')}`);"""
new_rt2 = """    if (hour < 9 || (hour === 9 && minute < 30)) {
      nextTradingTime.setHours(9, 30, 0, 0);
    } else if (hour >= 15) {
      nextTradingTime = nextTradingDay(new Date(nextTradingTime.getTime() + 86400000));
      nextTradingTime.setHours(9, 30, 0, 0);
    } else if (hour >= 12) {
      nextTradingTime.setHours(13, 0, 0, 0);
    }
    // 非交易日（节假日）排到下一交易日 9:30
    if (!isTradingDay(nextTradingTime)) {
      nextTradingTime = nextTradingDay(nextTradingTime);
      nextTradingTime.setHours(9, 30, 0, 0);
    }
    
    const delay = nextTradingTime.getTime() - now.getTime();
    console.log(`[实时分析] 非交易时间，下次分析: ${nextTradingTime.toLocaleString('zh-CN')}`);"""
assert s.count(old_rt2) == 1, 'realtime else block not found'
s = s.replace(old_rt2, new_rt2)

write(p, s)
print('ALL OK')
