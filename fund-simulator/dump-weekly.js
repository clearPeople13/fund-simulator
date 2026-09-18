const path = require('path');
const sqlite3 = require(path.join(process.cwd(), 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.get("SELECT period, content FROM reports WHERE user_id='default' AND report_type='weekly' ORDER BY id DESC LIMIT 1", (e, r) => {
  if (e) { console.error(e.message); process.exit(1); }
  console.log('period:', r.period);
  console.log(r.content.slice(0, 1000));
  db.close();
});
