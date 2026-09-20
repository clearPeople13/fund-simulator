# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js'
with io.open(p, 'r', encoding='utf-8') as f:
    c = f.read()

old = """    const sql = `INSERT INTO transactions (user_id, fund_code, transaction_type, amount, price, shares, fees, reason) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)`;
    
    db.run(sql, [
      userId,
      transaction.fund_code,
      transaction.action,
      transaction.amount,
      transaction.price,
      transaction.shares,
      transaction.fees || 0,
      transaction.reason
    ], function(err) {"""

new = """    const sql = `INSERT INTO transactions (user_id, fund_code, transaction_type, amount, price, shares, fees, reason, remaining_shares) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, CASE WHEN ? = 'BUY' THEN ? ELSE NULL END)`;
    
    db.run(sql, [
      userId,
      transaction.fund_code,
      transaction.action,
      transaction.amount,
      transaction.price,
      transaction.shares,
      transaction.fees || 0,
      transaction.reason,
      transaction.action,
      transaction.shares
    ], function(err) {"""

if old not in c:
    print('ERROR: anchor not found')
    raise SystemExit(1)
c = c.replace(old, new)
with io.open(p, 'w', encoding='utf-8', newline='') as f:
    f.write(c)
print('OK: saveTransaction 写入 remaining_shares')
