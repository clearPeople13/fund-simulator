const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('fund_simulator.db');

// 1. 清空旧分析结果
db.run('DELETE FROM ai_analysis', (err) => {
  if (err) console.error('清空 ai_analysis 失败:', err.message);
  else console.log('已清空旧分析结果（ai_analysis）');
  
  // 2. 查看当前观察池数量
  db.get('SELECT COUNT(*) as cnt FROM watchlist', (err, row) => {
    if (err) { console.error('watchlist 查询失败:', err.message); db.close(); return; }
    console.log(`观察池基金数量: ${row.cnt}`);
    
    // 3. 查看当前持仓
    db.get('SELECT COUNT(*) as cnt FROM holdings WHERE shares > 0', (err, row) => {
      if (err) { console.error('holdings 查询失败:', err.message); db.close(); return; }
      console.log(`持仓基金数量: ${row.cnt}`);
      db.close();
    });
  });
});
