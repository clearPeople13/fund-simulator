import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\backend\routes\ai.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = '''        await saveAnalysisResult(userId, code, analysisResults[code]);
      }
      aiAnalysisStatus.status = 'completed';'''
new = '''        await saveAnalysisResult(userId, code, analysisResults[code]);
        
        // AI 自动交易：BUY → 自动买入
        if (aiDecision === 'BUY') {
          console.log(`[AI交易] ${userId} ${code} AI 建议买入，自动执行...`);
          try {
            // 买入金额：总资产的 5%
            const portfolio = await getUserPortfolio(userId);
            const buyAmount = portfolio.total_assets * 0.05;
            const shares = buyAmount / entry;
            
            // 保存交易记录
            db.run('INSERT INTO transactions (user_id, fund_code, type, amount, shares, nav, transaction_date) VALUES (?, ?, "buy", ?, ?, ?, datetime("now"))',
              [userId, code, buyAmount, shares, entry]);
            
            // 更新持仓
            db.run('INSERT INTO holdings (user_id, fund_code, shares, cost, updated_at) VALUES (?, ?, ?, ?, datetime("now")) ON CONFLICT(user_id, fund_code) DO UPDATE SET shares = shares + ?, cost = cost + ?, updated_at = datetime("now")',
              [userId, code, shares, buyAmount, shares, buyAmount]);
            
            console.log(`[AI交易] ${userId} ${code} 买入成功：¥${buyAmount.toFixed(2)}，${shares.toFixed(2)} 份`);
          } catch (tradeErr) {
            console.error(`[AI交易] ${code} 买入失败: ${tradeErr.message}`);
          }
        }
      }
      aiAnalysisStatus.status = 'completed';'''
assert s.count(old) == 1
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('auto trade added')
