const s = require('sqlite3');
const db = new s.Database('C:/Users/jiancent/WorkBuddy/fund/fund-simulator/fund_simulator.db');
db.all("SELECT id, user_id, fund_code, order_type, amount, shares, price, fee, status, order_date FROM orders WHERE fund_code='005827' ORDER BY id", (e, r) => {
  console.log('orders:', JSON.stringify(r, null, 1));
  db.all("SELECT id, fund_code, transaction_type, amount, price, shares, fees, transaction_date FROM transactions WHERE fund_code='005827' ORDER BY id", (e2, t) => {
    console.log('transactions:', JSON.stringify(t, null, 1));
    db.close();
  });
});
