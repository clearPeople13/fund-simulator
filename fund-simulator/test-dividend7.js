const path = require('path');
const sqlite3 = require(path.join(process.cwd(), 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.all("SELECT nav_date, unit_nav, acc_nav FROM fund_nav WHERE fund_code='000001' AND acc_nav IS NOT NULL AND acc_nav > 0 ORDER BY nav_date", (e, r2) => {
  if (e) { console.error(e.message); process.exit(1); }
  let prevCum = null;
  const jumps = [];
  for (const row of r2) {
    const cum = +(row.acc_nav - row.unit_nav).toFixed(4);
    if (prevCum != null && Math.abs(cum - prevCum) > 0.0001) {
      jumps.push({ date: row.nav_date, per_unit: +(cum - prevCum).toFixed(4) });
    }
    prevCum = cum;
  }
  console.log('000001 cum 跳变次数:', jumps.length);
  jumps.forEach(j => console.log(j.date, '每份分红+', j.per_unit));
  db.close();
});
