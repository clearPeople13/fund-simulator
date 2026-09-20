const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.all("SELECT sql FROM sqlite_master WHERE name='fund_fees'", (e, r) => {
  if (e) { console.error(e.message); process.exit(1); }
  console.log(r[0] && r[0].sql);
  db.all("SELECT * FROM fund_fees", (e2, r2) => {
    if (e2) { console.error(e2.message); process.exit(1); }
    console.log(JSON.stringify(r2, null, 1).slice(0, 1600));
    db.close();
  });
});
