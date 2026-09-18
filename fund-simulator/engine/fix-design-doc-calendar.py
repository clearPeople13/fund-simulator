# -*- coding: utf-8 -*-
"""AI_FUND_OPERATIONS_DESIGN.md §3.1 交易日历：法定节假日已内置"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\AI_FUND_OPERATIONS_DESIGN.md"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = u"* 实现：isTradingWindow（本地工作日 09:00:00-15:05:59 允许下单；周末已排除；**法定节假日暂未内置**，如需完全对齐需引入节假日表 —— 遗留项）。"
new = u"* 实现：isTradingWindow（本地交易日 09:00:00-15:05:59 允许下单）；节假日表 engine/holidays.json（2026 已内置，国办发明电〔2025〕7号；每年 11 月公布次年安排后补充）；收盘前/收盘/盘中分析调度非交易日自动顺延下一交易日（nextTradingDay）；holidays 表存休市日供查询审计。"

assert s.count(old) == 1, 'target line not found'
s = s.replace(old, new)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('design doc updated')
