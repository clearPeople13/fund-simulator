const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.all("SELECT user_id, date, total_assets, daily_pnl, cash, market_value FROM portfolio_daily ORDER BY user_id, date", (e, r) => {
  if (e) { console.error(e.message); process.exit(1); }
  r.forEach(x => console.log(x.user_id, x.date, '总资产', x.total_assets.toFixed(2), '当日盈亏', x.daily_pnl.toFixed(2), '现金', x.cash.toFixed(2), '市值', x.market_value.toFixed(2)));
  db.close();
});
