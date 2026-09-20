// 回滚：删除验收用的 012414（watchlist + funds 行，fund_nav 真实净值保留）
const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.serialize(() => {
  db.run("DELETE FROM watchlist WHERE fund_code='012414'", function (e) {
    console.log('watchlist 删除:', e ? e.message : this.changes);
    db.run("DELETE FROM funds WHERE fund_code='012414'", function (e2) {
      console.log('funds 删除:', e2 ? e2.message : this.changes);
      db.all("SELECT COUNT(*) c FROM watchlist", (e3, r) => {
        console.log('watchlist 剩余:', r[0].c);
        db.all("SELECT COUNT(*) c FROM fund_nav WHERE fund_code='012414'", (e4, r2) => {
          console.log('fund_nav 012414 保留:', r2[0].c);
          db.close();
        });
      });
    });
  });
});
