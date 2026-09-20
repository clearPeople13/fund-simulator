// aggressive 账户数据核查：持仓/现金/已实现/订单/快照/绩效
const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.serialize(() => {
  console.log('=== holdings (aggressive) ===');
  db.all(`SELECT fund_code, shares, cost, total_cost, created_at FROM holdings WHERE user_id='aggressive'`, (e, r) => { console.log(r); });
  console.log('=== transactions (aggressive) 最近8条 ===');
  db.all(`SELECT id, transaction_type, fund_code, amount, price, shares, fees, transaction_date FROM transactions WHERE user_id='aggressive' ORDER BY id DESC LIMIT 8`, (e, r) => { console.log(r); });
  console.log('=== realized_pnl (aggressive) ===');
  db.all(`SELECT * FROM realized_pnl WHERE user_id='aggressive'`, (e, r) => { console.log(r); });
  console.log('=== orders (aggressive) ===');
  db.all(`SELECT id, fund_code, order_type, amount, shares, status, order_date, trade_date, fee FROM orders WHERE user_id='aggressive' ORDER BY id`, (e, r) => { console.log(r); });
  console.log('=== portfolio_daily (aggressive) 最近4条 ===');
  db.all(`SELECT date, total_assets, daily_pnl, cash, market_value FROM portfolio_daily WHERE user_id='aggressive' ORDER BY date DESC LIMIT 4`, (e, r) => { console.log(r); });
  console.log('=== performance_daily (aggressive) 最近4条 ===');
  db.all(`SELECT date, total_return, benchmark_return, excess_return FROM performance_daily WHERE user_id='aggressive' ORDER BY date DESC LIMIT 4`, (e, r) => { console.log(r); });
  db.close();
});
