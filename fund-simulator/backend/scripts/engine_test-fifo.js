/**
 * FIFO 分批赎回测试：模拟多次买入不同日期，卖出时按先进先出分档计费
 * 场景：005827（5档阶梯）
 *   - 30天前买入 10000（费率档 0.5%）
 *   - 2天前加仓 5000（费率档 1.5%）
 *   - 卖出 7000 份 → 先扣 30天前批次（0.5%）+ 剩余 2天前批次（1.5%）
 */
const s = require('sqlite3');
const db = new s.Database(':memory:');
const oe = require('./order-engine');
const feeM = require('./fee');

function run(sql, params = []) {
  return new Promise((res, rej) => db.run(sql, params, e => e ? rej(e) : res()));
}
function get(sql, params = []) {
  return new Promise((res, rej) => db.get(sql, params, (e, r) => e ? rej(e) : res(r)));
}
function all(sql, params = []) {
  return new Promise((res, rej) => db.all(sql, params, (e, r) => e ? rej(e) : res(r)));
}

(async () => {
  await run(`CREATE TABLE transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, fund_code TEXT, transaction_type TEXT,
    amount REAL, price REAL, shares REAL, fees REAL, reason TEXT, transaction_date TEXT, remaining_shares REAL)`);
  await run(`CREATE TABLE holdings (user_id TEXT, fund_code TEXT, shares REAL, cost_price REAL, total_cost REAL,
    created_at TEXT, updated_at TEXT)`);
  await run(`CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, fund_code TEXT, order_type TEXT,
    amount REAL, shares REAL, price REAL, fee REAL, status TEXT, order_date TEXT, confirm_date TEXT, reason TEXT, created_at TEXT)`);
  await run(`CREATE TABLE realized_pnl (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, fund_code TEXT, amount REAL, sell_fee REAL, note TEXT, created_at TEXT)`);
  await run(`CREATE TABLE fund_fees (fund_code TEXT PRIMARY KEY, buy_fee_pct REAL, sell_fee_7d REAL, sell_fee_1y REAL, sell_fee_ge1y REAL, sell_schedule TEXT, manage_fee_pct REAL, custody_fee_pct REAL, service_fee_pct REAL, updated_at TEXT)`);
  await run(`CREATE TABLE fund_nav (fund_code TEXT, nav_date TEXT, unit_nav REAL)`);
  await run(`INSERT INTO fund_fees (fund_code, buy_fee_pct, sell_schedule, manage_fee_pct, custody_fee_pct, service_fee_pct) VALUES (?,?,?,?,?,?)`,
    ['005827', 0.0015, JSON.stringify([{days:7,rate:0.015},{days:30,rate:0.0075},{days:365,rate:0.005},{days:730,rate:0.0025},{days:0,rate:0}]), 0.012, 0.002, 0]);

  // 两笔买入：30天前 10000 元 @1.50；2天前 5000 元 @1.60（内扣申购费）
  const b1 = feeM.calcBuyFee(10000, 0.0015);       // 14.98
  const b1s = Number(((10000 - b1) / 1.50).toFixed(4));   // 6656.68
  const b2 = feeM.calcBuyFee(5000, 0.0015);        // 7.49
  const b2s = Number(((5000 - b2) / 1.60).toFixed(4));    // 3120.32
  await run(`INSERT INTO transactions (user_id, fund_code, transaction_type, amount, price, shares, fees, reason, transaction_date, remaining_shares) VALUES (?,?,?,?,?,?,?,?,?,?)`,
    ['tester', '005827', 'BUY', 10000, 1.50, b1s, b1, 'buy1', '2026-08-18 09:00:00', b1s]);
  await run(`INSERT INTO transactions (user_id, fund_code, transaction_type, amount, price, shares, fees, reason, transaction_date, remaining_shares) VALUES (?,?,?,?,?,?,?,?,?,?)`,
    ['tester', '005827', 'BUY', 5000, 1.60, b2s, b2, 'buy2', '2026-09-15 09:00:00', b2s]);
  await run(`INSERT INTO holdings (user_id, fund_code, shares, cost_price, total_cost, created_at, updated_at) VALUES (?,?,?,?,?,?,?)`,
    ['tester', '005827', Number((b1s + b2s).toFixed(4)), 1.5342, 15000, '2026-08-18', '2026-09-15']);

  // 卖出订单：16号下单 7000 份，17号确认（T日净值=1.62）
  await run(`INSERT INTO orders (user_id, fund_code, order_type, amount, shares, price, fee, status, order_date, reason, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)`,
    ['tester', '005827', 'SELL', 0, 7000, 1.60, 0, 'SUBMITTED', '2026-09-16', 'test sell', '2026-09-16 10:00:00']);
  await run(`INSERT INTO fund_nav (fund_code, nav_date, unit_nav) VALUES ('005827','2026-09-16',1.62)`);

  const ctx = {
    db,
    saveTransaction: (uid, t) => run(`INSERT INTO transactions (user_id, fund_code, transaction_type, amount, price, shares, fees, reason, transaction_date, remaining_shares) VALUES (?,?,?,?,?,?,?,?,?, CASE WHEN ?='BUY' THEN ? ELSE NULL END)`,
      [uid, t.fund_code, t.action, t.amount, t.price, t.shares, t.fees || 0, t.reason, '2026-09-17 00:00:00', t.action, t.shares]),
    updateHolding: (uid, code, shares, costPrice, totalCost) => run(`UPDATE holdings SET shares=?, cost_price=?, total_cost=?, updated_at=? WHERE user_id=? AND fund_code=?`,
      [shares, costPrice, totalCost, '2026-09-17', uid, code]),
    audit: () => {}
  };

  const r = await oe.confirmPendingOrders(ctx, '2026-09-17');
  console.log('确认结果:', JSON.stringify(r));

  const tx = await all("SELECT id, transaction_type, amount, shares, fees, reason, remaining_shares FROM transactions ORDER BY id");
  console.log('transactions:', JSON.stringify(tx, null, 1));
  const rp = await all('SELECT * FROM realized_pnl');
  console.log('realized_pnl:', JSON.stringify(rp, null, 1));
  const h = await get('SELECT * FROM holdings WHERE fund_code=?', ['005827']);
  console.log('holdings:', JSON.stringify(h));

  // 断言
  const feeTotal = tx.find(t => t.transaction_type === 'SELL').fees;
  console.log('SELL 手续费 =', feeTotal, '（期望 ≈62.26 = 批1 0.5% + 批2 1.5%）');
  db.close();
})().catch(e => { console.error('失败:', e); db.close(); });
