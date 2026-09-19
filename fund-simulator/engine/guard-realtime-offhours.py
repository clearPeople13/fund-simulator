# -*- coding: utf-8 -*-
"""realtime 半小时分析加交易时段守卫：
1) 新增全局 isMarketOpenNow()
2) performAnalysis 开头：realtime 且盘外直接 return（不扫描/不选基/不下单）
3) setInterval 回调：检测到收盘/盘外 → clearInterval 并重新 schedule 到下一交易日 9:30
"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) isTradingDay 后加 isMarketOpenNow
old1 = """// 找到不小于 date 的第一个交易日 0 点
function nextTradingDay(date) {"""
new1 = """// 是否正在连续竞价时段（交易日 9:30-11:30 / 13:00-15:00）
function isMarketOpenNow(d = new Date()) {
  if (!isTradingDay(d)) return false;
  const h = d.getHours(), m = d.getMinutes();
  const mins = h * 60 + m;
  return (mins >= 570 && mins <= 690) || (mins >= 780 && mins <= 900); // 9:30=570, 11:30=690, 13:00=780, 15:00=900
}

// 找到不小于 date 的第一个交易日 0 点
function nextTradingDay(date) {"""
assert s.count(old1) == 1, 'anchor1'
s = s.replace(old1, new1)

# 2) setInterval 回调加守卫：盘外停 interval 并重排
old2 = """    setTimeout(() => {
      performAnalysis('realtime', true);
      // 之后每30分钟执行一次
      setInterval(() => performAnalysis('realtime', true), 30 * 60 * 1000);
    }, delay);"""
new2 = """    let realtimeTimer = null;
    setTimeout(() => {
      performAnalysis('realtime', true);
      // 之后每30分钟执行一次；检测到收盘/盘外自动停掉，重排到下一交易日 9:30
      realtimeTimer = setInterval(() => {
        if (!isMarketOpenNow()) {
          console.log('[实时分析] 已收盘/非交易时段，停止半小时循环，重排到下一交易日 9:30');
          clearInterval(realtimeTimer);
          scheduleRealtimeAnalysis();
          return;
        }
        performAnalysis('realtime', true);
      }, 30 * 60 * 1000);
    }, delay);"""
assert s.count(old2) == 1, 'anchor2'
s = s.replace(old2, new2)

# 3) performAnalysis 开头：realtime 盘外双保险
old3 = """  console.log(`\\n=== ${typeNames[analysisType]}开始 ===`);
  console.log(`时间: ${new Date().toLocaleString('zh-CN')}`);"""
new3 = """  // realtime 半小时分析双保险：非交易时段（周末/节假日/收盘后）直接跳过，不扫描/不选基/不下单
  if (analysisType === 'realtime' && auto && !isMarketOpenNow()) {
    console.log(`[实时分析] 非交易时段，跳过本次半小时分析`);
    return;
  }
  console.log(`\\n=== ${typeNames[analysisType]}开始 ===`);
  console.log(`时间: ${new Date().toLocaleString('zh-CN')}`);"""
assert s.count(old3) == 1, 'anchor3'
s = s.replace(old3, new3)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('market-open guard patched')
