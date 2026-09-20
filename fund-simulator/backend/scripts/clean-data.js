const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('C:\\Users\\jiancent\\WorkBuddy\\fund\\fund-simulator\\backend\\fund_simulator.db');

db.serialize(() => {
  // 重算 holdings：从 transactions 重新计算
  db.run('DELETE FROM holdings', (err) => {
    if (err) { console.error('clear holdings error:', err); return; }
    console.log('清空 holdings，从 transactions 重算...');

    db.all('SELECT user_id, fund_code, transaction_type, amount, shares FROM transactions ORDER BY id', (e2, txs) => {
      const holdings = {};
      txs.forEach(tx => {
        const key = `${tx.user_id}|${tx.fund_code}`;
        if (!holdings[key]) holdings[key] = { user_id: tx.user_id, fund_code: tx.fund_code, shares: 0, total_cost: 0 };
        if (tx.transaction_type === 'BUY') {
          holdings[key].shares += tx.shares;
          holdings[key].total_cost += tx.amount;
        } else if (tx.transaction_type === 'SELL') {
          const avgCost = holdings[key].shares > 0 ? holdings[key].total_cost / holdings[key].shares : 0;
          const sellShares = tx.amount / avgCost;
          holdings[key].shares -= sellShares;
          holdings[key].total_cost -= sellShares * avgCost;
        }
      });

      Object.values(holdings).forEach(h => {
        if (h.shares > 0.01) {
          const costPrice = h.total_cost / h.shares;
          db.run('INSERT INTO holdings (user_id, fund_code, shares, cost_price, total_cost, created_at, updated_at) VALUES (?, ?, ?, ?, ?, datetime("now"), datetime("now"))',
            [h.user_id, h.fund_code, h.shares, costPrice, h.total_cost]);
        }
      });

      console.log('\n=== 清洗后 holdings ===');
      db.all('SELECT user_id, fund_code, shares, cost_price, total_cost FROM holdings ORDER BY user_id', (e3, hs) => {
        hs.forEach(h => console.log(`  ${h.user_id} ${h.fund_code} ${Number(h.shares).toFixed(2)}份 成本价¥${Number(h.cost_price).toFixed(4)} 总成本¥${Number(h.total_cost).toFixed(2)}`));

        console.log('\n=== 清洗后 transactions ===');
        db.all('SELECT id, user_id, fund_code, transaction_type, amount FROM transactions ORDER BY id', (e4, txs2) => {
          txs2.forEach(t => console.log(`  tx#${t.id} ${t.user_id} ${t.transaction_type} ${t.fund_code} ¥${t.amount}`));

          console.log('\n=== 清洗后 orders ===');
          db.all('SELECT id, user_id, fund_code, order_type, status FROM orders ORDER BY id', (e5, orders2) => {
            orders2.forEach(o => console.log(`  order#${o.id} ${o.user_id} ${o.order_type} ${o.fund_code} [${o.status}]`));
            db.close();
            console.log('\n清洗完成！');
          });
        });
      });
    });
  });
});
