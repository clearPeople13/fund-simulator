const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('fund_simulator.db');
db.all("SELECT fund_code, fund_name, fund_type FROM funds WHERE fund_code IN ('481015','016262','005119','013841','013840','004320','021180','021179')", (e, funds) => {
  if (e) { console.log('ERR', e.message); return; }
  console.log('NEW FUNDS:', JSON.stringify(funds));
  let i = 0;
  const codes = funds.map(f => f.fund_code);
  for (const code of codes) {
    db.get('SELECT COUNT(*) n, MAX(nav_date) mx FROM fund_nav WHERE fund_code = ?', [code], (e2, r) => {
      console.log(code, 'nav count=', r.n, 'latest=', r.mx);
      if (++i === codes.length) {
        db.all('SELECT fund_code, COUNT(*) n FROM fund_nav WHERE fund_code IN (' + codes.map(() => '?').join(',') + ') GROUP BY fund_code', codes, (e3, rows) => {
          console.log('NAV SUMMARY:', JSON.stringify(rows));
        });
      }
    });
  }
});
