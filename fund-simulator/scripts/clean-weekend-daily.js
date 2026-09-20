const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('./fund_simulator.db');
// 删掉周末误生成的日报（period 为非交易日）
const weekend = ['2026-09-19', '2026-09-20'];
db.run(`DELETE FROM reports WHERE report_type='daily' AND period IN (?, ?)`, weekend, function (e) {
  if (e) { console.error(e.message); process.exit(1); }
  console.log('deleted weekend daily rows:', this.changes);
  db.all("SELECT id, user_id, period FROM reports WHERE report_type='daily' ORDER BY id", (e2, rows) => {
    rows.forEach(r => console.log('#' + r.id, r.user_id, r.period));
    db.close();
  });
});
