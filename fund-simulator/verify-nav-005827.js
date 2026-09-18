// 005827 最近净值 + 9/17 快照市值对证
const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.serialize(() => {
  console.log('=== fund_nav 005827 最近6条 ===');
  db.all(`SELECT nav_date, unit_nav, daily_return FROM fund_nav WHERE fund_code='005827' ORDER BY nav_date DESC LIMIT 6`, (e, r) => console.log(r));
  console.log('=== fund_nav 000001 最近6条 ===');
  db.all(`SELECT nav_date, unit_nav, daily_return FROM fund_nav WHERE fund_code='000001' ORDER BY nav_date DESC LIMIT 6`, (e, r) => console.log(r));
  console.log('=== portfolio_daily 生成时间（created_at 隐含）— 查 scheduler_runs ===');
  db.all(`SELECT run_type, started_at, finished_at, status FROM scheduler_runs ORDER BY id DESC LIMIT 6`, (e, r) => console.log(r));
  db.close();
});
