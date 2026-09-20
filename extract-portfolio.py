import io

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) 先删四个函数块（从 "function getUserPortfolio(userId) {" 到 "function saveAnalysisResult"）
start = s.find("function getUserPortfolio(userId) {")
end = s.find("function saveAnalysisResult(userId, fundCode, result) {", start)
assert start != -1 and end != -1
s = s[:start] + "// getUserPortfolio + saveTransaction + updateHolding + getAnalysisResults 已抽到 services/portfolio.js\n" + s[end:]

# 2) 加 require 在第1行后
old_line = "const express = require('express');"
new_line = """const express = require('express');
const { getUserPortfolio: getUserPortfolioRaw, saveTransaction: saveTransactionRaw, updateHolding: updateHoldingRaw, getAnalysisResults: getAnalysisResultsRaw } = require('./services/portfolio');"""
assert s.count(old_line) == 1
s = s.replace(old_line, new_line, 1)

# 3) 在 db 初始化后加包一层（找 "// 初始化数据库表" 之前）
db_init = s.find("// 初始化数据库表（幂等")
assert db_init != -1
wrap = """// 包一层：services 函数注入 ctx
function getUserPortfolio(userId) {
  return getUserPortfolioRaw({ db, userConfigs }, userId);
}
function saveTransaction(userId, transaction) {
  return saveTransactionRaw({ db }, userId, transaction);
}
function updateHolding(userId, fundCode, shares, costPrice, totalCost) {
  return updateHoldingRaw({ db }, userId, fundCode, shares, costPrice, totalCost);
}
function getAnalysisResults(userId) {
  return getAnalysisResultsRaw({ db }, userId);
}

"""
s = s[:db_init] + wrap + s[db_init:]

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('portfolio services extracted safely (order: delete first, then wrap)')
