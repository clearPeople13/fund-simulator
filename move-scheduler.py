import io

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) 删 /api/scheduler/run 块
start = s.find("// ============ P0-1 新增 API：订单/审计/调度状态 ============\napp.post('/api/scheduler/run'")
end = s.find("// /api/audit 已抽到 routes/readonly.js", start)
assert start != -1 and end != -1
s = s[:start] + "// /api/scheduler/run 已抽到 routes/system.js\n" + s[end:]

# 2) system 路由挂载 ctx 加新依赖
old_mount = "app.use('/api', require('./routes/system')({ aiAnalysisStatus, aiBus, isTradingDay, getAnalysisResults, getCurrentUser }));"
new_mount = "app.use('/api', require('./routes/system')({ aiAnalysisStatus, aiBus, isTradingDay, getAnalysisResults, getCurrentUser, db, userConfigs, computeFundProfiles, getRiskParams, rebalanceCheck, switchFunds, generateReport, performanceAttribution, generatePressureReport, confirmPendingOrders, performAnalysis, saveTransaction, updateHolding, audit }));"
assert s.count(old_mount) == 1
s = s.replace(old_mount, new_mount)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('scheduler/run moved')
