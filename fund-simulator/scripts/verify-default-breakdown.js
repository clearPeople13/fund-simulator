// default 累计收益 -242.54 组成拆解
const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.serialize(() => {
  console.log('=== realized_pnl (default) ===');
  db.all(`SELECT * FROM realized_pnl WHERE user_id='default'`, (e, r) => console.log(r));
  console.log('=== transactions (default) ===');
  db.all(`SELECT id, transaction_type, fund_code, amount, price, shares, fees, remaining_shares, transaction_date FROM transactions WHERE user_id='default' ORDER BY id`, (e, r) => console.log(r));
  console.log('=== holdings (default) ===');
  db.all(`SELECT fund_code, shares, cost_price, total_cost FROM holdings WHERE user_id='default'`, (e, r) => console.log(r));
  console.log('=== portfolio_daily (default) 全部 ===');
  db.all(`SELECT date, total_assets, daily_pnl, cash, market_value FROM portfolio_daily WHERE user_id='default' ORDER BY date`, (e, r) => console.log(r));
  console.log('=== orders (default) ===');
  db.all(`SELECT id, fund_code, order_type, amount, shares, status, order_date, fee FROM orders WHERE user_id='default' ORDER BY id`, (e, r) => console.log(r));
  db.close();
});
