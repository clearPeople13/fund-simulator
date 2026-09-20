const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('fund_simulator.db');
db.all("SELECT name FROM sqlite_master WHERE type='table'", (e, r) => {
  if (e) { console.log('ERR', e.message); return; }
  console.log(JSON.stringify(r.map(x => x.name)));
});
