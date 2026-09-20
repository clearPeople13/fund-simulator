// 修正 9/17 快照（成本口径→真实净值市值）+ 重算今日 —— v3（修参数绑定）
const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');

function localDateStr() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}
const all = (sql, args) => new Promise((resolve, reject) =>
  db.all(sql, args, (e, r) => e ? reject(e) : resolve(r)));
const one = (sql, args) => new Promise((resolve, reject) =>
  db.get(sql, args, (e, r) => e ? reject(e) : resolve(r)));
const run = (sql, args) => new Promise((resolve, reject) =>
  db.run(sql, args, function(e) { e ? reject(e) : resolve(this); }));

async function sharesAt(userId, date) {
  const txs = await all(
    `SELECT fund_code, transaction_type, shares FROM transactions
     WHERE user_id = ? AND date(transaction_date) <= ? ORDER BY transaction_date ASC, id ASC`, [userId, date]);
  const map = {};
  for (const t of txs) {
    if (t.transaction_type === 'BUY') map[t.fund_code] = (map[t.fund_code] || 0) + t.shares;
    else if (t.transaction_type === 'SELL') map[t.fund_code] = (map[t.fund_code] || 0) - t.shares;
  }
  return map;
}
async function cashAt(userId, date, initial) {
  const txs = await all(
    `SELECT transaction_type, amount, fees FROM transactions
     WHERE user_id = ? AND date(transaction_date) <= ?`, [userId, date]);
  let cash = initial;
  for (const t of txs) {
    if (t.transaction_type === 'BUY') cash -= t.amount;
    else if (t.transaction_type === 'SELL') cash += t.amount - t.fees;
  }
  return cash;
}
async function navAt(code, navDate) {
  const r = await one(`SELECT unit_nav FROM fund_nav WHERE fund_code = ? AND nav_date <= ? ORDER BY nav_date DESC LIMIT 1`, [code, navDate]);
  return r ? r.unit_nav : null;
}

(async () => {
  const today = localDateStr();
  const users = ['default', 'aggressive'];
  const init = 100000;

  for (const uid of users) {
    // 9/17：份额=截至9/17交易，净值=9/17
    const sh17 = await sharesAt(uid, '2026-09-17');
    let mv17 = 0;
    for (const [code, sh] of Object.entries(sh17)) {
      if (sh <= 0) continue;
      const nav = await navAt(code, '2026-09-17');
      if (nav) mv17 += sh * nav;
    }
    const cash17 = await cashAt(uid, '2026-09-17', init);
    const total17 = cash17 + mv17;
    const pnl17 = total17 - init;
    const u1 = await run(`UPDATE portfolio_daily SET total_assets=?, daily_pnl=?, cash=?, market_value=? WHERE user_id=? AND date='2026-09-17'`,
      [total17, pnl17, cash17, mv17, uid]);
    console.log(`${uid}: 9/17 total=${total17.toFixed(2)} pnl=${pnl17.toFixed(2)} cash=${cash17.toFixed(2)} mv=${mv17.toFixed(2)} (changed=${u1.changes})`);

    // 今日：份额=当前持仓，净值=最新(<=today)
    const holdings = await all(`SELECT fund_code, shares FROM holdings WHERE user_id=?`, [uid]);
    let mv18 = 0;
    for (const h of holdings) {
      const nav = await navAt(h.fund_code, today);
      if (nav) mv18 += h.shares * nav;
    }
    const cash18 = await cashAt(uid, today, init);
    const total18 = cash18 + mv18;
    const pnl18 = total18 - total17;
    const u2 = await run(`UPDATE portfolio_daily SET total_assets=?, daily_pnl=?, cash=?, market_value=? WHERE user_id=? AND date=?`,
      [total18, pnl18, cash18, mv18, uid, today]);
    console.log(`${uid}: ${today} total=${total18.toFixed(2)} pnl=${pnl18.toFixed(2)} cash=${cash18.toFixed(2)} mv=${mv18.toFixed(2)} (changed=${u2.changes})`);
  }

  console.log('\n最终 portfolio_daily:');
  const rows = await all(`SELECT user_id, date, total_assets, daily_pnl, cash, market_value FROM portfolio_daily ORDER BY user_id, date`, []);
  rows.forEach(r => console.log(`${r.user_id} | ${r.date} | total=${r.total_assets.toFixed(2)} | pnl=${r.daily_pnl.toFixed(2)} | cash=${r.cash.toFixed(2)} | mv=${r.market_value.toFixed(2)}`));
  db.close();
})().catch(e => { console.error('ERR', e); db.close(); });
