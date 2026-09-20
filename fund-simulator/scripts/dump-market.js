const path = require('path');
const sqlite3 = require(path.join(process.cwd(), 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.all("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%benchmark%' OR name LIKE '%index%' OR name='market_env'", (e, t) => {
  if (e) { console.error(e.message); process.exit(1); }
  console.log('相关表:', t.map(x => x.name));
  db.all("PRAGMA table_info(benchmark_daily)", (e2, cols) => {
    if (e2) { console.error(e2.message); process.exit(1); }
    console.log('benchmark_daily 列:', cols.map(c => c.name + ':' + c.type).join(', '));
    db.all("SELECT * FROM benchmark_daily ORDER BY date DESC LIMIT 3", (e3, r) => {
      if (e3) { console.error(e3.message); process.exit(1); }
      console.log('最近3行:', JSON.stringify(r));
      db.all("SELECT * FROM market_env", (e4, m) => {
        if (e4) { console.error(e4.message); process.exit(1); }
        console.log('market_env:', JSON.stringify(m));
        db.close();
      });
    });
  });
});
