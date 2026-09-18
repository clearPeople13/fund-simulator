# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js'
c = io.open(p, encoding='utf-8').read()

anchor = """      reason TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);
    db.run(`CREATE TABLE IF NOT EXISTS fund_fees ("""
migration = """      reason TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);

    // 旧库迁移：orders.trade_date（T 日确认净值日；历史订单默认等于下单日，行为不变）
    db.run(`ALTER TABLE orders ADD COLUMN trade_date TEXT`, (err) => {
      if (!err) {
        db.run(`UPDATE orders SET trade_date = order_date WHERE trade_date IS NULL OR trade_date = ''`, (e) => {
          if (e) console.error('orders.trade_date 回填失败:', e.message);
        });
      }
    });

    db.run(`CREATE TABLE IF NOT EXISTS fund_fees ("""
assert c.count(anchor) == 1, 'anchor %d' % c.count(anchor)
c = c.replace(anchor, migration, 1)

io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
