const path = require('path');
const sqlite3 = require(path.join(process.cwd(), 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.run("INSERT INTO analysis_logs (user_id, analysis_type, fund_code, decision, confidence, entry_price, target_price, stop_loss, analysis_time, signal_label, signal_reason) VALUES ('default','hotspot','HOTSPOT','温和走强',1.28,0,0,0,datetime('now'),'医药/医疗','医药/医疗 温和走强（日 +0.75%），AI 继续持有跟踪。')",
  function (e) {
    if (e) { console.error(e.message); process.exit(1); }
    console.log('inserted, changes:', this.changes);
    db.close();
  });
