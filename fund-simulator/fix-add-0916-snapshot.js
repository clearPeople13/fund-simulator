const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
// 补 9/16 账户快照（建仓日）：T+1 当日持仓按成本计市值，当日盈亏 0
const rows = [
  // user_id, date, total_assets, daily_pnl, cash, market_value
  ['default', '2026-09-16', 100000.00, 0, 80000.9496, 19999.0504],
  ['aggressive', '2026-09-16', 100000.00, 0, 64001.8221, 35998.1779]
];
let done = 0;
rows.forEach(r => {
  db.run(`INSERT INTO portfolio_daily (user_id, date, total_assets, daily_pnl, cash, market_value) VALUES (?, ?, ?, ?, ?, ?)
          ON CONFLICT(user_id, date) DO UPDATE SET total_assets=excluded.total_assets, daily_pnl=excluded.daily_pnl, cash=excluded.cash, market_value=excluded.market_value`,
    r, function (e) {
      if (e) { console.error(e.message); process.exit(1); }
      done++;
      if (done === rows.length) {
        db.all('SELECT user_id, date, total_assets, daily_pnl, cash, market_value FROM portfolio_daily ORDER BY user_id, date', (e2, r2) => {
          if (e2) { console.error(e2.message); process.exit(1); }
          console.log(JSON.stringify(r2, null, 1));
          db.close();
        });
      }
    });
});
