const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3'));
const dbPath = path.join(__dirname, 'fund_simulator.db');
const db = new sqlite3.Database(dbPath);
db.all("SELECT name FROM pragma_table_info('orders')", (e, cols) => {
  if (e) { console.error('cols ERR', e.message); return; }
  console.log('cols:', cols.map(r => r.name).join(','));
  db.all('SELECT id, order_date, trade_date, status, order_type, fund_code FROM orders ORDER BY id DESC LIMIT 6', (e2, rows) => {
    if (e2) { console.error('rows ERR', e2.message); return; }
    console.log(JSON.stringify(rows, null, 1));
    db.get("SELECT COUNT(*) c FROM orders WHERE trade_date IS NULL OR trade_date = ''", (e3, r3) => {
      console.log('null trade_date count:', e3 ? e3.message : r3.c);
      db.close();
    });
  });
});
