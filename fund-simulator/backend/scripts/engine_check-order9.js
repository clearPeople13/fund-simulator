const s = require('sqlite3');
const db = new s.Database('C:/Users/jiancent/WorkBuddy/fund/fund-simulator/fund_simulator.db');
db.get("SELECT * FROM orders WHERE id=9", (e, r) => {
  console.log('orders id=9:', JSON.stringify(r, null, 1));
  db.get("SELECT * FROM orders WHERE id=7", (e2, r2) => {
    console.log('orders id=7:', JSON.stringify(r2, null, 1));
    db.close();
  });
});
