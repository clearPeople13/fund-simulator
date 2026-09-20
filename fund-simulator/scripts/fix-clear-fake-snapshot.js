const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
// 删除今日（2026-09-18）伪快照：当日净值未公布，该快照是用 T-1 净值估算的，等 21:30 净值同步后自动重建
db.run("DELETE FROM portfolio_daily WHERE date = '2026-09-18'", function (e) {
  if (e) { console.error(e.message); process.exit(1); }
  console.log('deleted', this.changes, 'rows');
  db.all('SELECT user_id, date, daily_pnl FROM portfolio_daily ORDER BY user_id, date', (e2, r) => {
    if (e2) { console.error(e2.message); process.exit(1); }
    console.log(JSON.stringify(r));
    db.close();
  });
});
