const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.all("SELECT fund_code, unit_nav, nav_date, day_return FROM fund_universe WHERE fund_code IN ('005827','000001','161725','005267')", (e, r) => {
  console.log('fund_universe:', JSON.stringify(r, null, 1));
  db.all("SELECT fund_code, unit_nav, nav_date FROM fund_nav WHERE fund_code IN ('005827','000001','161725','005267') AND nav_date=(SELECT MAX(nav_date) FROM fund_nav)", (e2, r2) => {
    console.log('fund_nav 最新:', JSON.stringify(r2, null, 1));
    db.close();
  });
});
