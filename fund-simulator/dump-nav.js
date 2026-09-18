const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.all("SELECT fund_code, nav_date, unit_nav, daily_return FROM fund_nav WHERE nav_date >= '2026-09-16' ORDER BY nav_date, fund_code", (e, r) => {
  if (e) { console.error(e.message); process.exit(1); }
  console.log(JSON.stringify(r, null, 1));
  db.close();
});
