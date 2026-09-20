// 检查 012414 是否已入 watchlist / funds
const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.all(`SELECT user_id, fund_code, source, reason FROM watchlist WHERE fund_code='012414'`, (e, r) => {
  console.log('watchlist 012414:', r);
  db.get(`SELECT fund_code, fund_name, fund_type FROM funds WHERE fund_code='012414'`, (e2, f) => {
    console.log('funds 012414:', f);
    db.get(`SELECT COUNT(*) c FROM fund_nav WHERE fund_code='012414'`, (e3, n) => {
      console.log('fund_nav 012414 条数:', n ? n.c : '?');
      db.close();
    });
  });
});
