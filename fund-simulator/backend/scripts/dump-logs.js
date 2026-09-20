const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
const tables = ['analysis_logs', 'audit_logs', 'risk_events', 'scheduler_runs'];
let left = tables.length;
tables.forEach(t => {
  db.all(`SELECT COUNT(*) c FROM ${t}`, (e, r) => {
    if (e) { console.log(t, 'ERR', e.message); }
    else {
      console.log(t, 'rows:', r[0].c);
      db.all(`SELECT * FROM ${t} ORDER BY id DESC LIMIT 2`, (e2, r2) => {
        if (!e2 && r2 && r2.length) console.log('  sample:', JSON.stringify(r2[0]).slice(0, 400));
        if (--left === 0) db.close();
      });
    }
  });
});
