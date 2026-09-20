const path = require('path');
const sqlite3 = require(path.join(process.cwd(), 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.all('PRAGMA table_info(fund_universe)', (e, r) => {
  if (e) { console.error(e.message); process.exit(1); }
  console.log('fund_universe 列:', r.map(c => c.name).join(', '));
  db.all('SELECT COUNT(*) c FROM dividends', (e2, r2) => {
    console.log('dividends 条数:', r2[0].c);
    db.all('SELECT * FROM dividends LIMIT 2', (e3, r3) => {
      console.log('dividends 样例:', JSON.stringify(r3[0] || null).slice(0, 300));
      db.close();
    });
  });
});
