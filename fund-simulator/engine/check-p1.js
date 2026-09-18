const s = require('sqlite3');
const db = new s.Database('C:/Users/jiancent/WorkBuddy/fund/fund-simulator/fund_simulator.db');
db.all('SELECT fund_code, volatility, downside_risk, style_label, score FROM fund_profiles ORDER BY score DESC LIMIT 8', (e, r) => {
  console.log('=== 基金画像(前8) ===');
  r.forEach(x => console.log(x.fund_code, x.style_label, 'score=' + x.score, 'vol=' + x.volatility + '%'));
  db.all("SELECT report_type, COUNT(*) c FROM reports GROUP BY report_type", (e2, r2) => {
    console.log('=== 报告 ===');
    r2.forEach(x => console.log(x.report_type, x.c + '份'));
    db.all('SELECT fund_code, style_label, score FROM fund_profiles', (e3, r3) => {
      console.log('=== 全部画像 ===');
      r3.forEach(x => console.log(x.fund_code, x.style_label, x.score));
      db.close();
    });
  });
});
