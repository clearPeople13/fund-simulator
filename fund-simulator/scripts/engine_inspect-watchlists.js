const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('fund_simulator.db');
db.all("SELECT * FROM user_configs", (e, users) => {
  if (e) { console.log('ERR', e.message); return; }
  console.log('USER_CONFIGS:', JSON.stringify(users, null, 1));
  let i = 0;
  const keys = users ? users.map(u => u.id || u.user_id || u.key) : [];
  users.forEach((u) => {
    const uid = u.id !== undefined ? u.id : u.user_id;
    if (uid === undefined) { i++; if (i === users.length) done(); return; }
    db.all('SELECT * FROM watchlist WHERE user_id = ?', [uid], (e2, w) => {
      console.log('watchlist user_id=' + uid + ':', JSON.stringify(w));
      i++; if (i === users.length) done();
    });
  });
  function done() {
    db.all('SELECT * FROM portfolios', (e3, p) => { console.log('PORTFOLIOS:', JSON.stringify(p)); });
  }
});
