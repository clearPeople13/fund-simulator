const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('fund_simulator.db');
const codes = ['011369','001437','001198','720001','024459','162214','005119','004320','021179','007490','001411','013840','005844','002910','481015'];
db.all("SELECT f.fund_code, f.fund_name, f.fund_type, (SELECT COUNT(*) FROM fund_nav n WHERE n.fund_code=f.fund_code) nav_n, (SELECT MAX(nav_date) FROM fund_nav n WHERE n.fund_code=f.fund_code) nav_latest FROM funds f WHERE f.fund_code IN ('" + codes.join("','") + "') ORDER BY f.fund_code", (e, rows) => {
  if (e) { console.log('ERR', e.message); return; }
  console.log('FUNDS+NAV:');
  for (const r of rows) console.log(r.fund_code, r.fund_name, '[' + r.fund_type + ']', 'nav=' + r.nav_n, 'latest=' + r.nav_latest);
  // 检查 A/C 去重是否生效：同策略基金只应出现一个
  db.all("SELECT w.user_id, w.fund_code, f.fund_name FROM watchlist w JOIN funds f ON f.fund_code=w.fund_code WHERE w.source='ai' ORDER BY w.user_id", (e2, rows2) => {
    if (e2) { console.log('ERR2', e2.message); return; }
    console.log('AI WATCHLIST ALL:');
    for (const r of rows2) console.log(r.user_id, r.fund_code, r.fund_name);
  });
});
