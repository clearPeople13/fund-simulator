const s = require('sqlite3');
const db = new s.Database('C:/Users/jiancent/WorkBuddy/fund/fund-simulator/fund_simulator.db');
// 回滚：000001 订单保持 17 号下单（18 号确认，T+1 待确认逻辑正确）
db.run("UPDATE orders SET order_date='2026-09-17' WHERE id=1 AND fund_code='000001'", function (err) {
  console.log('回滚 000001 订单:', err ? err.message : 'OK ' + this.changes + ' 笔');
  db.all("SELECT id, fund_code, order_type, order_date, status FROM orders ORDER BY id", (e, r) => {
    console.log('orders 全表:', JSON.stringify(r, null, 1));
    db.close();
  });
});
