const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('fund_simulator.db');

// 把旧的 DATETIME 转成时间戳（毫秒）
db.run(`UPDATE transactions SET transaction_date = strftime('%s', transaction_date) * 1000 WHERE typeof(transaction_date) = 'text'`, (err) => {
  if (err) console.error('迁移失败:', err);
  else console.log('旧数据迁移完成');
  
  // 验证
  db.all('SELECT transaction_date, typeof(transaction_date) as type FROM transactions LIMIT 5', (err, rows) => {
    if (err) console.error(err);
    else rows.forEach(r => console.log(r.transaction_date, r.type));
    db.close();
  });
});
