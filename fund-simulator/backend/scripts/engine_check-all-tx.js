const s = require('sqlite3');
const db = new s.Database('C:/Users/jiancent/WorkBuddy/fund/fund-simulator/fund_simulator.db');
db.all("SELECT id, user_id, fund_code, transaction_type, amount, price, shares, fees, transaction_date FROM transactions ORDER BY id", (e, r) => {
  console.log(JSON.stringify(r, null, 1));
  db.close();
});
