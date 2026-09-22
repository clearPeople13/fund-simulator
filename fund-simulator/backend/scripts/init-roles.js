// 建 ai_roles 表 + 写入默认角色（用 sqlite3）
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const dbPath = path.join(__dirname, '..', 'fund_simulator.db');
const db = new sqlite3.Database(dbPath);

db.serialize(() => {
  db.run(`
    CREATE TABLE IF NOT EXISTS ai_roles (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      avatar TEXT DEFAULT '👤',
      style TEXT NOT NULL,
      description TEXT DEFAULT '',
      initial_capital REAL DEFAULT 100000,
      risk_tolerance TEXT DEFAULT 'medium',
      target_return REAL DEFAULT 0.10,
      stop_loss REAL DEFAULT 0.05,
      take_profit REAL DEFAULT 0.20,
      max_position REAL DEFAULT 0.60,
      max_single_fund REAL DEFAULT 0.20,
      min_hold_funds INTEGER DEFAULT 3,
      max_drawdown REAL DEFAULT 0.10,
      exit_drawdown INTEGER DEFAULT 15,
      exit_style TEXT DEFAULT 'timely',
      entry_signal_threshold TEXT DEFAULT 'strong',
      buy_ratio REAL DEFAULT 0.2,
      add_ratio REAL DEFAULT 0.1,
      add_cooldown_days INTEGER DEFAULT 5,
      rebalance_frequency TEXT DEFAULT 'monthly',
      watchlist_style TEXT DEFAULT '均衡分散/大盘蓝筹',
      base_weights TEXT DEFAULT '{}',
      created_at INTEGER DEFAULT (strftime('%s','now')*1000)
    )
  `, (err) => {
    if (err) { console.error('建表失败:', err); process.exit(1); }
    
    db.get('SELECT COUNT(*) as c FROM ai_roles', (err, row) => {
      if (err) { console.error('查询失败:', err); process.exit(1); }
      
      if (row.c === 0) {
        const insertSql = `INSERT INTO ai_roles 
          (id, name, avatar, style, description, initial_capital, risk_tolerance, target_return,
           stop_loss, take_profit, max_position, max_single_fund, min_hold_funds, max_drawdown,
           exit_drawdown, exit_style, entry_signal_threshold, buy_ratio, add_ratio, add_cooldown_days,
           rebalance_frequency, watchlist_style, base_weights)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`;
        
        db.run(insertSql, [
          'default', '默认用户', '👤', '稳健型', '稳健投资，追求长期稳定收益',
          100000, 'medium', 0.10, 0.05, 0.20, 0.60, 0.20, 3, 0.10, 15, 'timely', 'strong',
          0.2, 0.1, 5, 'monthly', '均衡分散/大盘蓝筹',
          JSON.stringify({'混合型': 0.5, '股票型': 0.3, '指数型': 0.2})
        ], () => {
          db.run(insertSql, [
            'aggressive', '激进用户', '🚀', '激进型', '追求高收益，愿意承担更高风险',
            100000, 'high', 0.20, 0.10, 0.40, 1.00, 0.40, 2, 0.20, 25, 'patient', 'medium',
            0.2, 0.1, 3, 'weekly', '成长/主题/高弹性',
            JSON.stringify({'混合型': 0.4, '股票型': 0.5, '指数型': 0.1})
          ], () => {
            console.log('已插入 2 个默认角色');
            listRoles();
          });
        });
      } else {
        console.log(`ai_roles 表已有 ${row.c} 个角色`);
        listRoles();
      }
    });
  });
});

function listRoles() {
  db.all('SELECT id, name, avatar, style, description FROM ai_roles', (err, rows) => {
    if (err) { console.error('查询失败:', err); }
    else console.log('当前角色：', rows);
    db.close();
  });
}
