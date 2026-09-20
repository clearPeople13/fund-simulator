const s = require('sqlite3');
const db = new s.Database('C:/Users/jiancent/WorkBuddy/fund/fund-simulator/fund_simulator.db');
db.all("SELECT sql FROM sqlite_master WHERE name='fund_fees'", (e, r) => {
  console.log(JSON.stringify(r, null, 1));
  db.close();
});
