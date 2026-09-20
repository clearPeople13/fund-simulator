const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.all("SELECT id, user_id, fund_code, order_type, amount, shares, price, fee, status, order_date, trade_date FROM orders ORDER BY id DESC LIMIT 10", (e, r) => {
  if (e) { console.error(e.message); process.exit(1); }
  console.log(JSON.stringify(r, null, 1));
  db.close();
});
