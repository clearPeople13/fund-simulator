const s = require('sqlite3');
const db = new s.Database('C:/Users/jiancent/WorkBuddy/fund/fund-simulator/fund_simulator.db');
const fixes = [
  { code: '005827', buy: 0.0015 },
  { code: '161725', buy: 0.001 },
  { code: '000001', buy: 0.0015 },
  { code: '005267', buy: 0.0015 }
];
let n = 0;
fixes.forEach(f => {
  db.run('UPDATE fund_fees SET buy_fee_pct=? WHERE fund_code=?', [f.buy, f.code], (e) => {
    if (e) console.error(f.code, e.message); else { console.log(f.code, 'buy_fee_pct ->', f.buy); n++; }
  });
});
setTimeout(() => {
  db.all('SELECT fund_code, buy_fee_pct, sell_schedule, manage_fee_pct, custody_fee_pct FROM fund_fees', (e, r) => {
    console.log(JSON.stringify(r, null, 1));
    db.close();
  });
}, 400);
