const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('fund_simulator.db');

function run(sql, params) {
  return new Promise((resolve, reject) => {
    db.run(sql, params, function (err) { err ? reject(err) : resolve(this.changes); });
  });
}

(async () => {
  // 清洗规则：删除所有 source='ai' 的观察项，若该基金被其他用户观察（watchlist 任意源）或持仓（holdings shares>0）
  const users = ['default', 'aggressive'];
  for (const u of users) {
    const others = users.filter(x => x !== u);
    const cond = others.map(o => `fund_code IN (SELECT fund_code FROM watchlist WHERE user_id='${o}') OR fund_code IN (SELECT fund_code FROM holdings WHERE user_id='${o}' AND shares > 0)`).join(' OR ');
    const n = await run(`DELETE FROM watchlist WHERE user_id = ? AND source = 'ai' AND (${cond})`, [u]);
    console.log(`${u}: 删除重叠 AI 观察项 ${n} 条`);
  }
  // 打印清洗后结果
  db.all('SELECT user_id, fund_code, source FROM watchlist ORDER BY user_id', (e, rows) => {
    if (e) { console.log('ERR', e.message); return; }
    const byUser = {};
    for (const r of rows) (byUser[r.user_id] = byUser[r.user_id] || []).push(r.fund_code + '(' + r.source[0] + ')');
    for (const [u, list] of Object.entries(byUser)) console.log(u + ':', list.join(', '));
    const sets = {};
    for (const r of rows) (sets[r.user_id] = sets[r.user_id] || new Set()).add(r.fund_code);
    const ids = Object.keys(sets);
    if (ids.length === 2) {
      const inter = [...sets[ids[0]]].filter(x => sets[ids[1]].has(x));
      console.log('REMAIN OVERLAP:', JSON.stringify(inter));
    }
  });
})();
