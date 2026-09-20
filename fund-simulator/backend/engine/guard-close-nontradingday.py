# -*- coding: utf-8 -*-
"""pre_close/close 加交易日守卫：非交易日（周末/节假日）跳过，不生成空日报"""
import io

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """  // realtime 半小时分析双保险：非交易时段（周末/节假日/收盘后）直接跳过，不扫描/不选基/不下单
  if (analysisType === 'realtime' && auto && !isMarketOpenNow()) {
    console.log(`[实时分析] 非交易时段，跳过本次半小时分析`);
    return;
  }"""
new = """  // realtime 半小时分析双保险：非交易时段（周末/节假日/收盘后）直接跳过，不扫描/不选基/不下单
  if (analysisType === 'realtime' && auto && !isMarketOpenNow()) {
    console.log(`[实时分析] 非交易时段，跳过本次半小时分析`);
    return;
  }
  // pre_close/close 是交易日收盘任务：非交易日（周末/节假日）直接跳过，不生成空日报/不写快照
  if ((analysisType === 'pre_close' || analysisType === 'close') && auto && !isTradingDay()) {
    console.log(`[${analysisType}] 非交易日（周末/节假日），跳过`);
    return;
  }"""
assert s.count(old) == 1, 'guard block not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('pre_close/close trading-day guard added')
