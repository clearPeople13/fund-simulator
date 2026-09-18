const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.all("SELECT fund_code, fund_name, latest_nav FROM funds WHERE fund_code IN ('005827','000001','161725','005267')", (e, r) => {
  console.log(r);
  db.close();
});
