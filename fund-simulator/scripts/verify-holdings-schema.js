// holdings 表结构 + aggressive 持仓实际数据 + 前端用哪个 API
const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.serialize(() => {
  db.all("PRAGMA table_info(holdings)", (e, r) => {
    console.log('holdings schema:', e ? e.message : r.map(c => c.name).join(','));
  });
  db.all("SELECT * FROM holdings", (e, r) => {
    console.log('holdings all rows:', e ? 'ERR ' + e.message : r);
  });
  db.close();
});
