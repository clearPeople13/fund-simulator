const s = require('sqlite3');
const path = 'C:/Users/jiancent/WorkBuddy/fund/fund-simulator/fund_simulator.db';
const db = new s.Database(path);

function run(sql, params) {
  return new Promise((res, rej) => db.run(sql, params, e => e ? rej(e) : res()));
}
function get(sql, params) {
  return new Promise((res, rej) => db.get(sql, params, (e, r) => e ? rej(e) : res(r)));
}

(async () => {
  // 1. fund_fees 加 sell_schedule 列
  const cols = await get("SELECT sql FROM sqlite_master WHERE name='fund_fees'");
  if (!cols.sql.includes('sell_schedule')) {
    await run("ALTER TABLE fund_fees ADD COLUMN sell_schedule TEXT");
    console.log('fund_fees 增加 sell_schedule 列');
  }

  // 2. 插入/更新 4 只基金真实费率
  const fees = [
    { code: '005827', buy: 0.0015, schedule: JSON.stringify([{days:7,rate:0.015},{days:30,rate:0.0075},{days:365,rate:0.005},{days:730,rate:0.0025},{days:0,rate:0}]), manage: 0.012, custody: 0.002, service: 0 },
    { code: '161725', buy: 0.001,  schedule: JSON.stringify([{days:7,rate:0.015},{days:365,rate:0.005},{days:0,rate:0.0025}]), manage: 0.01, custody: 0.0022, service: 0 },
    { code: '000001', buy: 0.0015, schedule: JSON.stringify([{days:7,rate:0.015},{days:0,rate:0.005}]), manage: 0.012, custody: 0.002, service: 0 },
    { code: '005267', buy: 0.0015, schedule: JSON.stringify([{days:7,rate:0.015},{days:30,rate:0.0075},{days:365,rate:0.005},{days:730,rate:0.0025},{days:0,rate:0}]), manage: 0.012, custody: 0.002, service: 0 }
  ];
  for (const f of fees) {
    await run(`INSERT INTO fund_fees (fund_code, buy_fee_pct, sell_fee_7d, sell_fee_1y, sell_fee_ge1y, sell_schedule, manage_fee_pct, custody_fee_pct, service_fee_pct, updated_at)
               VALUES (?, 0.015, 0.015, 0.005, 0.0025, ?, ?, ?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(fund_code) DO UPDATE SET
                 buy_fee_pct=excluded.buy_fee_pct, sell_schedule=excluded.sell_schedule,
                 manage_fee_pct=excluded.manage_fee_pct, custody_fee_pct=excluded.custody_fee_pct, service_fee_pct=excluded.service_fee_pct, updated_at=CURRENT_TIMESTAMP`,
      [f.code, f.schedule, f.manage, f.custody, f.service]);
    console.log('费率写入:', f.code, 'buy=' + f.buy, 'schedule=' + f.schedule);
  }

  // 3. 重新校准历史交易（内扣法申购费 + 净额份额）
  // 内扣申购费 = 金额 - 金额/(1+费率)；份额 = (金额-费)/净值
  function buyFix(amount, rate, price) {
    const fee = Number((amount - amount / (1 + rate)).toFixed(2));
    const shares = Number(((amount - fee) / price).toFixed(4));
    return { fee, shares };
  }
  const b1 = buyFix(19999.0504, 0.0015, 1.4888);  // 005827 default
  const b2 = buyFix(19999.4915, 0.001, 0.5279);   // 161725 aggressive
  const b3 = buyFix(15998.6864, 0.0015, 2.2508);  // 005267 aggressive
  const b4 = buyFix(8000, 0.0015, 1.296);         // 000001 default
  console.log('内扣申购费:', b1, b2, b3, b4);

  await run('UPDATE transactions SET fees=?, shares=? WHERE id=1', [b2.fee, b2.shares]);
  await run('UPDATE transactions SET fees=?, shares=? WHERE id=2', [b3.fee, b3.shares]);
  await run('UPDATE transactions SET fees=?, shares=? WHERE id=3', [b1.fee, b1.shares]);
  await run('UPDATE transactions SET fees=?, shares=? WHERE id=4', [b4.fee, b4.shares]);
  console.log('transactions 已更新（内扣法）');

  // 4. 重建持仓
  // 005827：买入 b1.shares 份（总成本 19999.05），卖出 6717 份 → 剩余
  const soldShares = 6717;
  const soldCost = Number((19999.0504 * (soldShares / b1.shares)).toFixed(2));
  const remainShares = Number((b1.shares - soldShares).toFixed(4));
  const remainCost = Number((19999.0504 - soldCost).toFixed(2));
  const remainPrice = Number((remainCost / remainShares).toFixed(4));
  const realized = Number((9850.27 - soldCost).toFixed(2)); // 净额 9850.27 - 卖出成本
  console.log('005827 卖出成本', soldCost, '剩余', remainShares, remainCost, remainPrice, 'realized', realized);
  await run('UPDATE holdings SET shares=?, cost_price=?, total_cost=? WHERE user_id=? AND fund_code=?', [remainShares, remainPrice, remainCost, 'default', '005827']);
  await run('UPDATE holdings SET shares=?, cost_price=?, total_cost=? WHERE user_id=? AND fund_code=?', [b2.shares, Number((19999.4915 / b2.shares).toFixed(4)), 19999.4915, 'aggressive', '161725']);
  await run('UPDATE holdings SET shares=?, cost_price=?, total_cost=? WHERE user_id=? AND fund_code=?', [b3.shares, Number((15998.6864 / b3.shares).toFixed(4)), 15998.6864, 'aggressive', '005267']);
  await run('UPDATE holdings SET shares=?, cost_price=?, total_cost=? WHERE user_id=? AND fund_code=?', [b4.shares, Number((8000 / b4.shares).toFixed(4)), 8000, 'default', '000001']);
  console.log('holdings 已重建');

  // 5. 更新已实现盈亏
  await run("UPDATE realized_pnl SET amount=?, note='真实费率校准：005827卖出确认（6717份，净额9850.27-含费成本" + soldCost.toFixed(2) + "，内扣申购费29.95）' WHERE id=1", [realized]);
  console.log('realized_pnl 已更新:', realized);

  // 6. 校验输出
  const all = await new Promise((res, rej) => db.all("SELECT id,user_id,fund_code,transaction_type,amount,fees,shares FROM transactions ORDER BY id", (e, r) => e ? rej(e) : res(r)));
  console.log(JSON.stringify(all, null, 1));
  const hs = await new Promise((res, rej) => db.all("SELECT user_id,fund_code,shares,cost_price,total_cost FROM holdings ORDER BY user_id", (e, r) => e ? rej(e) : res(r)));
  console.log(JSON.stringify(hs, null, 1));
  db.close();
})().catch(e => { console.error('失败:', e); db.close(); });
