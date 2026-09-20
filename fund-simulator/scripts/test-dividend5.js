const path = require('path');
const sqlite3 = require(path.join(process.cwd(), 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
// 检查 fund_nav 有无 acc_nav 数据 + cum 序列跳变（分红推导）
db.all("SELECT fund_code, COUNT(*) c, SUM(CASE WHEN acc_nav IS NOT NULL AND acc_nav > 0 THEN 1 ELSE 0 END) has_acc FROM fund_nav GROUP BY fund_code", (e, r) => {
  if (e) { console.error(e.message); process.exit(1); }
  r.forEach(x => console.log(x.fund_code, '总数', x.c, '有acc_nav', x.has_acc));
  // 005827 cum 序列跳变
  db.all("SELECT nav_date, unit_nav, acc_nav FROM fund_nav WHERE fund_code='005827' AND acc_nav IS NOT NULL AND acc_nav > 0 ORDER BY nav_date", (e2, r2) => {
    if (e2) { console.error(e2.message); process.exit(1); }
    let prevCum = null;
    const jumps = [];
    for (const row of r2) {
      const cum = +(row.acc_nav - row.unit_nav).toFixed(4);
      if (prevCum != null && Math.abs(cum - prevCum) > 0.0001) {
        jumps.push({ date: row.nav_date, cum_before: prevCum, cum_after: cum, per_unit: +(cum - prevCum).toFixed(4) });
      }
      prevCum = cum;
    }
    console.log('005827 cum 跳变次数:', jumps.length);
    jumps.slice(0, 8).forEach(j => console.log(j.date, '每份分红+', j.per_unit));
    db.close();
  });
});
