const path = require('path');
const sqlite3 = require(path.join(process.cwd(), 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.all("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name", (e, r) => {
  if (e) { console.error(e.message); process.exit(1); }
  console.log('表:', r.map(x => x.name).join(', '));
  db.all('PRAGMA table_info(fund_profiles)', (e2, r2) => {
    if (e2) { console.error(e2.message); process.exit(1); }
    console.log('fund_profiles 列:', r2.map(c => c.name).join(', '));
    db.close();
  });
});
