const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.all("SELECT fund_code, fund_name, manager, inception_date, benchmark, fund_type FROM funds WHERE fund_code IN ('005827','161725','000001','005267')", (e, r) => {
  if (e) { console.error(e.message); process.exit(1); }
  console.log(JSON.stringify(r, null, 1));
  db.close();
});
