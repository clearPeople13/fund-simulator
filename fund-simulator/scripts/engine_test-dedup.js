const s = require('sqlite3');
const db = new s.Database('C:/Users/jiancent/WorkBuddy/fund/fund-simulator/fund_simulator.db');
db.get("SELECT COUNT(*) c FROM orders WHERE user_id='default' AND fund_code='005827' AND order_type='SELL' AND order_date >= date('now','-7 day')", (e, r) => {
  console.log('SQL count:', JSON.stringify(r));
  db.get("SELECT date('now') d, date('now','-7 day') d7", (e2, r2) => {
    console.log('dates:', JSON.stringify(r2));
    db.all("SELECT id, order_date, order_type, status FROM orders WHERE fund_code='005827'", (e3, r3) => {
      console.log('005827 orders:', JSON.stringify(r3));
      db.close();
    });
  });
});
