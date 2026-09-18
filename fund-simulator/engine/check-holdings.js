const s = require('sqlite3');
const db = new s.Database('C:/Users/jiancent/WorkBuddy/fund/fund-simulator/fund_simulator.db');
db.all("SELECT fund_code, shares, cost_price, total_cost FROM holdings WHERE user_id='default'", (e, r) => {
  console.log('holdings:', JSON.stringify(r, null, 1));
  db.all("SELECT COUNT(*) n FROM realized_pnl", (e2, r2) => {
    console.log('realized_pnl 行数:', r2[0].n);
    db.close();
  });
});
