const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.all("SELECT sql FROM sqlite_master WHERE name='analysis_logs'", (e, r) => {
  console.log(r[0].sql);
  db.get("SELECT COUNT(*) c FROM analysis_logs", (e2, r2) => {
    console.log('rows:', r2.c);
    db.all("SELECT * FROM analysis_logs ORDER BY rowid DESC LIMIT 2", (e3, r3) => {
      r3.forEach(x => console.log(JSON.stringify(x).slice(0, 300)));
      db.close();
    });
  });
});
