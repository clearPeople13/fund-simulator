const s = require('sqlite3');
const db = new s.Database('C:/Users/jiancent/WorkBuddy/fund/fund-simulator/fund_simulator.db');

function run(sql, params) {
  return new Promise((res, rej) => db.run(sql, params, e => e ? rej(e) : res()));
}
function get(sql, params) {
  return new Promise((res, rej) => db.get(sql, params, (e, r) => e ? rej(e) : res(r)));
}

(async () => {
  // 1. 加列
  const cols = await get("SELECT sql FROM sqlite_master WHERE name='transactions'");
  if (!cols.sql.includes('remaining_shares')) {
    await run('ALTER TABLE transactions ADD COLUMN remaining_shares REAL');
    console.log('transactions 增加 remaining_shares 列');
  }
  // 2. 初始化：历史 BUY 剩余份额 = 当前持仓对应份额
  const init = [
    { id: 1, rem: 37847.1519 },   // 161725 aggressive（未卖）
    { id: 2, rem: 7097.3549 },    // 005267 aggressive（未卖）
    { id: 3, rem: 6695.8831 },    // 005827 default（已卖 6717）
    { id: 4, rem: 6163.5957 }     // 000001 default（未卖）
  ];
  for (const i of init) {
    await run('UPDATE transactions SET remaining_shares=? WHERE id=?', [i.rem, i.id]);
    console.log('tx id=' + i.id + ' remaining_shares=' + i.rem);
  }
  // 3. 校验
  const all = await new Promise((res, rej) => db.all("SELECT id,fund_code,transaction_type,shares,remaining_shares FROM transactions ORDER BY id", (e, r) => e ? rej(e) : res(r)));
  console.log(JSON.stringify(all, null, 1));
  db.close();
})().catch(e => { console.error('失败:', e); db.close(); });
