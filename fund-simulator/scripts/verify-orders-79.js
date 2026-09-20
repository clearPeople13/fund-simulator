const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3'));
const db = new sqlite3.Database(path.join(__dirname, 'fund_simulator.db'));
db.all("SELECT id, user_id, fund_code, order_type, amount, status, order_date, trade_date, reason, created_at FROM orders WHERE id IN (7,9) ORDER BY id", (e, rows) => {
  if (e) { console.error('ERR', e.message); return; }
  console.log(JSON.stringify(rows, null, 1));
  db.close();
});
