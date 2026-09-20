const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3'));
const db = new sqlite3.Database(path.join(__dirname, 'fund_simulator.db'));
db.all("SELECT id, user_id, fund_code, transaction_type, amount, transaction_date FROM transactions ORDER BY id", (e, rows) => {
  if (e) { console.error('ERR', e.message); return; }
  console.log('=== transactions (DB raw) ===');
  rows.forEach(r => console.log(`${r.id} ${r.user_id} ${r.transaction_type} ${r.fund_code} ¥${r.amount} @ ${r.transaction_date}`));
  console.log('now UTC:', new Date().toISOString(), ' now local:', new Date().toString());
  db.all("SELECT id, user_id, fund_code, order_type, status, order_date, trade_date, created_at FROM orders ORDER BY id", (e2, r2) => {
    if (e2) { console.error('ERR2', e2.message); return; }
    console.log('=== orders ===');
    r2.forEach(o => console.log(`${o.id} ${o.order_type} ${o.fund_code} ${o.status} order=${o.order_date} trade=${o.trade_date} created=${o.created_at}`));
    db.close();
  });
});
