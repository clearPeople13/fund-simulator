const path = require('path');
const sqlite3 = require(path.join(process.cwd(), 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
// 每个 (user_id, report_type, period) 只保留最大 id（最新一份），删其余重复
db.run(`DELETE FROM reports WHERE id NOT IN (
  SELECT MAX(id) FROM reports GROUP BY user_id, report_type, period
)`, function (e) {
  if (e) { console.error(e.message); process.exit(1); }
  console.log('deleted rows:', this.changes);
  db.all("SELECT report_type, COUNT(*) c FROM reports GROUP BY report_type", (e2, rows) => {
    rows.forEach(r => console.log(r.report_type, r.c));
    db.all("SELECT id, user_id, report_type, period FROM reports ORDER BY id DESC LIMIT 12", (e3, rows3) => {
      rows3.forEach(r => console.log(`#${r.id} ${r.user_id} ${r.report_type} ${r.period}`));
      db.close();
    });
  });
});
