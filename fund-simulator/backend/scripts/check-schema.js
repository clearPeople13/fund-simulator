const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('C:\\Users\\jiancent\\WorkBuddy\\fund\\fund-simulator\\backend\\fund_simulator.db');
db.all("PRAGMA table_info(holdings)", (e, cols) => {
  cols.forEach(c => console.log(c.name, c.type));
  db.close();
});
