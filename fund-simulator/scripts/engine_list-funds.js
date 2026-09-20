const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('fund_simulator.db');
db.all('SELECT fund_code, fund_name, fund_type FROM funds ORDER BY fund_type, fund_code', (e, rows) => {
  if (e) { console.log('ERR', e.message); return; }
  for (const r of rows) console.log(r.fund_type + ' | ' + r.fund_code + ' | ' + r.fund_name);
});
