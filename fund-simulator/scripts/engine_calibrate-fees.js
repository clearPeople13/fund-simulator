const s = require('sqlite3');
const db = new s.Database('C:/Users/jiancent/WorkBuddy/fund/fund-simulator/fund_simulator.db');

function calcShares(amount, fee, price) {
  return Number(((amount - fee) / price).toFixed(4));
}

// ---- 1. 交易记录补申购费 + 按净额重建份额 ----
const buyFixes = [
  { id: 1, fee: 30.00, shares: calcShares(19999.4915, 30.00, 0.5279) },   // 161725
  { id: 2, fee: 24.00, shares: calcShares(15998.6864, 24.00, 2.2508) },   // 005267
  { id: 3, fee: 30.00, shares: calcShares(19999.0504, 30.00, 1.4888) }    // 005827
];
let done = 0;
buyFixes.forEach(f => {
  db.run('UPDATE transactions SET fees=?, shares=? WHERE id=?', [f.fee, f.shares, f.id], (err) => {
    if (err) console.error('tx ' + f.id + ' 失败:', err.message);
    else { console.log('tx id=' + f.id + ' fee=' + f.fee + ' shares=' + f.shares); done++; }
  });
});

setTimeout(() => {
  // ---- 2. 重建持仓（成本=含费总投入/份额）----
  // default 005827：买入13412.97份，卖出6717份（成本按比例）
  const buyShares = buyFixes[2].shares; // 13412.97
  const buyCost = 19999.0504;
  const soldShares = 6717;
  const soldCost = Number((buyCost * (soldShares / buyShares)).toFixed(2));
  const remainShares = Number((buyShares - soldShares).toFixed(4));
  const remainCost = Number((buyCost - soldCost).toFixed(2));
  const remainPrice = Number((remainCost / remainShares).toFixed(4));
  console.log('005827 卖出成本:', soldCost, '剩余:', remainShares, remainCost, remainPrice);
  const realized = Number((9850.27 - soldCost).toFixed(2)); // 净额9850.27 - 卖出成本
  console.log('005827 realized:', realized);

  db.run('UPDATE holdings SET shares=?, cost_price=?, total_cost=? WHERE user_id=? AND fund_code=?',
    [remainShares, remainPrice, remainCost, 'default', '005827'], (err) => {
      console.log('holdings 005827:', err ? err.message : 'OK');
    });

  db.run('UPDATE holdings SET shares=?, cost_price=?, total_cost=? WHERE user_id=? AND fund_code=?',
    [buyFixes[0].shares, Number((19999.4915 / buyFixes[0].shares).toFixed(4)), 19999.4915, 'aggressive', '161725'], (err) => {
      console.log('holdings 161725:', err ? err.message : 'OK');
    });

  db.run('UPDATE holdings SET shares=?, cost_price=?, total_cost=? WHERE user_id=? AND fund_code=?',
    [buyFixes[1].shares, Number((15998.6864 / buyFixes[1].shares).toFixed(4)), 15998.6864, 'aggressive', '005267'], (err) => {
      console.log('holdings 005267:', err ? err.message : 'OK');
    });

  // ---- 3. 更新已实现盈亏（005827 卖出）----
  db.run("UPDATE realized_pnl SET amount=?, note='校准重建：2026-09-18卖出确认（6717份，净额9850.27-成本" + soldCost.toFixed(2) + "，含申购费30）' WHERE id=1", [realized], (err) => {
    console.log('realized_pnl:', err ? err.message : 'OK amount=' + realized);
  });

  setTimeout(() => {
    db.all("SELECT * FROM holdings ORDER BY user_id", (e, h) => {
      console.log('holdings 结果:', JSON.stringify(h, null, 1));
      db.all("SELECT * FROM realized_pnl", (e2, rp) => {
        console.log('realized_pnl:', JSON.stringify(rp, null, 1));
        db.close();
      });
    });
  }, 500);
}, 500);
