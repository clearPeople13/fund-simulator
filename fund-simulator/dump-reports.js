const path = require('path');
const sqlite3 = require(path.join(process.cwd(), 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.all("SELECT report_type, COUNT(*) c, MAX(created_at) last FROM reports GROUP BY report_type", (e, r) => {
  if (e) { console.error(e.message); process.exit(1); }
  console.log(JSON.stringify(r, null, 1));
  db.close();
});
