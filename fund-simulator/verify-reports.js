// 读 default 最新月报内容（验证归因小节 + 9 月数据）
const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.all(`SELECT id, user_id, report_type, period, content FROM reports
        WHERE user_id='default' AND report_type='monthly' ORDER BY id DESC LIMIT 1`, (e, r) => {
  if (e) { console.error(e.message); process.exit(1); }
  if (!r.length) { console.log('no monthly report'); process.exit(0); }
  const c = r[0].content || '';
  console.log('period:', r[0].period, '| len:', c.length);
  // 打印关键小节
  const lines = c.split('\n');
  const keys = ['归因', '配置贡献', '选基贡献', '总超额', '压力', '回撤', '报告期'];
  lines.forEach(l => {
    if (keys.some(k => l.includes(k))) console.log('  >', l.trim().slice(0, 150));
  });
  db.close();
});
