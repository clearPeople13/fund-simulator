const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.all("SELECT sql FROM sqlite_master WHERE name IN ('realized_pnl','transactions','holdings')", (e, r) => {
  if (e) { console.error(e.message); process.exit(1); }
  r.forEach(x => console.log(x.sql, '\n---'));
  db.all('SELECT * FROM realized_pnl', (e2, r2) => {
    if (e2) { console.error(e2.message); process.exit(1); }
    console.log('realized_pnl rows:', JSON.stringify(r2));
    db.close();
  });
});
