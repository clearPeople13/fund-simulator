const s = require('sqlite3');
const db = new s.Database('C:/Users/jiancent/WorkBuddy/fund/fund-simulator/fund_simulator.db');

// 1. transactions：17号买入 → 16号（保留时间部分）
db.run("UPDATE transactions SET transaction_date = '2026-09-16' || substr(transaction_date, 11) WHERE transaction_type='BUY' AND transaction_date LIKE '2026-09-17%'", function (err) {
  if (err) { console.error('transactions 更新失败:', err.message); db.close(); return; }
  console.log('transactions 买入改16号:', this.changes, '笔');
});

// 2. orders：BUY 订单 order_date 同步
db.all("SELECT id, user_id, fund_code, order_type, order_date, status FROM orders WHERE order_type='BUY' AND order_date='2026-09-17'", (e, rows) => {
  if (e) { console.error('orders 查询失败:', e.message); db.close(); return; }
  console.log('orders 17号BUY:', JSON.stringify(rows));
  let done = 0;
  rows.forEach(r => {
    db.run("UPDATE orders SET order_date='2026-09-16' WHERE id=?", [r.id], (e2) => {
      if (!e2) done++;
    });
  });
  setTimeout(() => {
    console.log('orders BUY 已改:', done, '笔');
    // 3. 输出验证
    db.all("SELECT user_id, fund_code, transaction_type, price, shares, transaction_date FROM transactions WHERE transaction_date LIKE '2026-09-16%' ORDER BY user_id", (e3, t) => {
      console.log('16号交易:', JSON.stringify(t, null, 1));
      db.close();
    });
  }, 300);
});
