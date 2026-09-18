const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('fund_simulator.db');
db.all("SELECT fund_code, fund_name, inception_date, scale, unit_nav FROM fund_universe WHERE fund_code IN ('025208','025209','013312','162214','481015','005844')", (e, rows) => {
  if (e) { console.log('ERR', e.message); return; }
  console.log('UNIVERSE ROWS:', JSON.stringify(rows, null, 1));
});
db.all("SELECT w.user_id, w.fund_code, w.source, w.reason FROM watchlist w WHERE w.user_id='aggressive' ORDER BY w.source, w.fund_code", (e2, rows2) => {
  if (e2) { console.log('ERR2', e2.message); return; }
  console.log('AGGRESSIVE WATCHLIST ROWS:', JSON.stringify(rows2, null, 1));
});
