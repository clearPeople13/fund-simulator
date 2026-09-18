const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('fund_simulator.db');
db.all('SELECT user_id, fund_code, shares FROM holdings WHERE shares > 0 ORDER BY user_id', (e, rows) => {
  if (e) { console.log('ERR', e.message); return; }
  const by = {};
  for (const r of rows) (by[r.user_id] = by[r.user_id] || []).push(r.fund_code + ':' + r.shares);
  for (const [u, l] of Object.entries(by)) console.log(u, 'holdings:', l.join(', '));
});
