const path = require('path');
const sqlite3 = require(path.join(process.cwd(), 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.all("SELECT sql FROM sqlite_master WHERE name='reports'", (e, rows) => {
  console.log(rows[0].sql);
  db.all("SELECT * FROM reports ORDER BY rowid DESC LIMIT 25", (e2, rows2) => {
    console.log('---rows---');
    rows2.forEach(r => console.log(JSON.stringify(r).slice(0, 180)));
    db.all("SELECT report_type, COUNT(*) c FROM reports GROUP BY report_type", (e3, rows3) => {
      console.log('---counts---');
      rows3.forEach(r => console.log(r.report_type, r.c));
      db.close();
    });
  });
});
