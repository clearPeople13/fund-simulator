const s = require('sqlite3');
const db = new s.Database('C:/Users/jiancent/WorkBuddy/fund/fund-simulator/fund_simulator.db');
db.all("SELECT fund_code, fund_name, fund_type FROM funds WHERE fund_code='000001'", (e, r) => {
  console.log(JSON.stringify(r, null, 1));
  db.close();
});
