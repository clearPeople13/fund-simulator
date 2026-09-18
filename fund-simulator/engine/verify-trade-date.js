const db = require('better-sqlite3')('fund_simulator.db');
const cols = db.prepare("SELECT name FROM pragma_table_info('orders')").all().map(r => r.name);
console.log('cols:', cols.join(','));
const rows = db.prepare('SELECT id, order_date, trade_date, status, order_type, fund_code FROM orders ORDER BY id DESC LIMIT 6').all();
console.log(JSON.stringify(rows, null, 1));
// 空 trade_date 检查
const bad = db.prepare("SELECT COUNT(*) c FROM orders WHERE trade_date IS NULL OR trade_date = ''").get();
console.log('null trade_date count:', bad.c);
db.close();
