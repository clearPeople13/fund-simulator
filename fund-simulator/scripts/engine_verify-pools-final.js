const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('fund_simulator.db');
db.all("SELECT w.user_id, w.fund_code, f.fund_name, f.fund_type, (SELECT COUNT(*) FROM fund_nav n WHERE n.fund_code=f.fund_code) nav_n, (SELECT MAX(nav_date) FROM fund_nav n WHERE n.fund_code=f.fund_code) nav_latest FROM watchlist w JOIN funds f ON f.fund_code=w.fund_code WHERE w.source='ai' ORDER BY w.user_id, w.fund_code", (e, rows) => {
  if (e) { console.log('ERR', e.message); return; }
  for (const r of rows) console.log(r.user_id.padEnd(10), r.fund_code, r.fund_name.padEnd(28), '[' + r.fund_type + ']', 'nav=' + r.nav_n, 'latest=' + r.nav_latest);
});
