# -*- coding: utf-8 -*-
import io, re

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js'
c = io.open(p, encoding='utf-8').read()

# 1. performAnalysis 加 auto 参数（调度触发才下单；手动"立即分析"只出决策）
old = "async function performAnalysis(analysisType) {"
new = "async function performAnalysis(analysisType, auto = false) {"
assert c.count(old) == 1, 'sig %d' % c.count(old)
c = c.replace(old, new, 1)

# 2. 买入下单条件：任何周期分析（auto）信号 buy/add 即下单（盘中实时/14:30预收盘/15:00收盘）
old2 = """        if (analysisType === 'close' && (action === 'buy' || action === 'add') && currentNav > 0) {"""
new2 = """        if (auto && (action === 'buy' || action === 'add') && currentNav > 0) {"""
assert c.count(old2) == 1, 'buy cond %d' % c.count(old2)
c = c.replace(old2, new2, 1)

# 3. 退场（SELL）也只在 AI 周期触发时执行（手动触发不产生交易）
old3 = """    if (analysisType === 'close') {
      for (const userId of Object.keys(userConfigs)) {
        try {
          const userCfg = await getRiskParams(userId);
          const pf = await getUserPortfolio(userId);"""
new3 = """    if (analysisType === 'close' && auto) {
      for (const userId of Object.keys(userConfigs)) {
        try {
          const userCfg = await getRiskParams(userId);
          const pf = await getUserPortfolio(userId);"""
assert c.count(old3) == 1, 'exit cond %d' % c.count(old3)
c = c.replace(old3, new3, 1)

# 4. 调度触发传 auto=true（实时/预收盘/收盘）
old4 = "      performAnalysis('realtime');\n      // 之后每30分钟执行一次\n      setInterval(() => performAnalysis('realtime'), 30 * 60 * 1000);"
new4 = "      performAnalysis('realtime', true);\n      // 之后每30分钟执行一次\n      setInterval(() => performAnalysis('realtime', true), 30 * 60 * 1000);"
assert c.count(old4) == 1, 'realtime %d' % c.count(old4)
c = c.replace(old4, new4, 1)

old5 = "    performAnalysis('pre_close');\n    // 每天执行一次\n    setInterval(() => performAnalysis('pre_close'), 24 * 60 * 60 * 1000);"
new5 = "    performAnalysis('pre_close', true);\n    // 每天执行一次\n    setInterval(() => performAnalysis('pre_close', true), 24 * 60 * 60 * 1000);"
assert c.count(old5) == 1, 'preclose %d' % c.count(old5)
c = c.replace(old5, new5, 1)

old6 = "    performAnalysis('close');\n    // 每天执行一次\n    setInterval(() => performAnalysis('close'), 24 * 60 * 60 * 1000);"
new6 = "    performAnalysis('close', true);\n    // 每天执行一次\n    setInterval(() => performAnalysis('close', true), 24 * 60 * 60 * 1000);"
assert c.count(old6) == 1, 'close %d' % c.count(old6)
c = c.replace(old6, new6, 1)

# 5. orders 表加 trade_date（T 日确认净值日）
old7 = "      order_date TEXT,\n      confirm_date TEXT,"
new7 = "      order_date TEXT,\n      trade_date TEXT,\n      confirm_date TEXT,"
assert c.count(old7) == 1, 'orders col %d' % c.count(old7)
c = c.replace(old7, new7, 1)

io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('server OK')
