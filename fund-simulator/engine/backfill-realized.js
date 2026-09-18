const s = require('sqlite3');
const db = new s.Database('C:/Users/jiancent/WorkBuddy/fund/fund-simulator/fund_simulator.db');
db.run("INSERT INTO realized_pnl (user_id, fund_code, amount, sell_fee, note) VALUES ('default', '005827', -149.26, 150, '历史补记：2026-09-18卖出确认（6717份@1.4888，净额9850.27-成本9999.53）')", function (err) {
  console.log('补记:', err ? err.message : 'OK id=' + this.lastID);
  db.all("SELECT SUM(amount) t FROM realized_pnl", (e, r) => {
    console.log('realized 合计:', r[0].t);
    db.close();
  });
});
