const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('fund_simulator.db');
const codes = ['007490','002051','001411','025209','025208','017811','005844','002910'];
db.all("SELECT fund_code, fund_name, fund_type FROM funds WHERE fund_code IN ('" + codes.join("','") + "')", (e, funds) => {
  if (e) { console.log('ERR', e.message); return; }
  console.log('NEW FUNDS:', JSON.stringify(funds, null, 0));
  const codes2 = funds.map(f => f.fund_code);
  let i = 0;
  for (const code of codes2) {
    db.get('SELECT COUNT(*) n, MAX(nav_date) mx, MIN(nav_date) mn FROM fund_nav WHERE fund_code = ?', [code], (e2, r) => {
      console.log(code, 'nav=', r.n, 'range', r.mn, '->', r.mx);
      if (++i === codes2.length) {
        db.all("SELECT fund_code, source FROM watchlist WHERE user_id='aggressive' ORDER BY source, fund_code", (e3, rows) => {
          console.log('AGGRESSIVE WATCHLIST:', JSON.stringify(rows));
        });
        db.all("SELECT fund_code, source FROM watchlist WHERE user_id='default' ORDER BY source, fund_code", (e4, rows2) => {
          console.log('DEFAULT WATCHLIST:', JSON.stringify(rows2));
        });
      }
    });
  }
});
