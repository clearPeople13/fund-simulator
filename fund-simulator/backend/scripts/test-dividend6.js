const path = require('path');
const sqlite3 = require(path.join(process.cwd(), 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.all("SELECT nav_date, unit_nav, acc_nav FROM fund_nav WHERE fund_code='005827' ORDER BY nav_date LIMIT 3", (e, r1) => {
  if (e) { console.error(e.message); process.exit(1); }
  console.log('005827 最早3行:', JSON.stringify(r1));
  db.all("SELECT nav_date, unit_nav, acc_nav FROM fund_nav WHERE fund_code='005827' ORDER BY nav_date DESC LIMIT 3", (e2, r2) => {
    if (e2) { console.error(e2.message); process.exit(1); }
    console.log('005827 最新3行:', JSON.stringify(r2));
    db.all("SELECT nav_date, unit_nav, acc_nav FROM fund_nav WHERE fund_code='000001' AND nav_date BETWEEN '2020-01-01' AND '2020-03-31' ORDER BY nav_date LIMIT 5", (e3, r3) => {
      if (e3) { console.error(e3.message); process.exit(1); }
      console.log('000001 2020年初:', JSON.stringify(r3));
      db.close();
    });
  });
});
