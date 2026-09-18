const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('fund_simulator.db');
db.all('SELECT user_id, fund_code, reason, source FROM watchlist ORDER BY user_id', (e, rows) => {
  if (e) { console.log('ERR', e.message); return; }
  const byUser = {};
  for (const r of rows) {
    (byUser[r.user_id] = byUser[r.user_id] || []).push(r);
  }
  for (const [u, list] of Object.entries(byUser)) {
    console.log('=== ' + u + ' (' + list.length + ') ===');
    for (const r of list) console.log('  ' + r.fund_code + ' | ' + r.source + ' | ' + (r.reason || '').slice(0, 40));
  }
  // 重叠检查
  const sets = {};
  for (const r of rows) (sets[r.user_id] = sets[r.user_id] || new Set()).add(r.fund_code);
  const ids = Object.keys(sets);
  if (ids.length === 2) {
    const inter = [...sets[ids[0]]].filter(x => sets[ids[1]].has(x));
    console.log('OVERLAP:', JSON.stringify(inter));
  }
});
