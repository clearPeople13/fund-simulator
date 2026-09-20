const s = require('sqlite3');
const db = new s.Database('C:/Users/jiancent/WorkBuddy/fund/fund-simulator/fund_simulator.db');
db.all("SELECT user_id, fund_code, transaction_type, amount, price, shares, fees, transaction_date FROM transactions WHERE transaction_date LIKE '2026-09-17%' OR transaction_date LIKE '2026-09-16%' ORDER BY user_id, transaction_date", (e, r) => {
  console.log('transactions 16-17号:');
  console.log(JSON.stringify(r, null, 1));
  db.all("SELECT user_id, fund_code, shares, cost_price, total_cost FROM holdings ORDER BY user_id", (e2, h) => {
    console.log('holdings:');
    console.log(JSON.stringify(h, null, 1));
    db.close();
  });
});
