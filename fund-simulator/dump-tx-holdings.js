const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.all("SELECT user_id, transaction_type, fund_code, amount, fees, shares, price, transaction_date FROM transactions ORDER BY user_id, transaction_date", (e, r) => {
  if (e) { console.error(e.message); process.exit(1); }
  console.log(JSON.stringify(r, null, 1));
  db.all("SELECT user_id, fund_code, shares, total_cost, cost_price FROM holdings", (e2, r2) => {
    if (e2) { console.error(e2.message); process.exit(1); }
    console.log('holdings:', JSON.stringify(r2, null, 1));
    db.close();
  });
});
