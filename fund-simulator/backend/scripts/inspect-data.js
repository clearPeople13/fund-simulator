const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('C:\\Users\\jiancent\\WorkBuddy\\fund\\fund-simulator\\backend\\fund_simulator.db');

const fmt = (ts) => {
  if (!ts) return 'null';
  const d = new Date(Number(ts));
  const bj = new Date(d.toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }));
  return bj.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' });
};

console.log('=== transactions ===');
db.all('SELECT id, user_id, fund_code, transaction_type, amount, price, shares, transaction_date FROM transactions ORDER BY id', (e, rows) => {
  rows.forEach(t => {
    console.log(`#${t.id} ${t.user_id} ${t.transaction_type} ${t.fund_code} ¥${Number(t.amount).toFixed(2)} | ${fmt(t.transaction_date)}`);
  });

  console.log('\n=== orders ===');
  db.all('SELECT id, user_id, fund_code, order_type, amount, status, order_date, trade_date FROM orders ORDER BY id', (e2, orders) => {
    orders.forEach(o => {
      console.log(`#${o.id} ${o.user_id} ${o.order_type} ${o.fund_code} ¥${Number(o.amount).toFixed(2)} [${o.status}] order=${o.order_date} trade=${o.trade_date}`);
    });

    console.log('\n=== holdings ===');
    db.all('SELECT user_id, fund_code, shares, cost FROM holdings ORDER BY user_id', (e3, hs) => {
      hs.forEach(h => {
        console.log(`${h.user_id} ${h.fund_code} ${Number(h.shares).toFixed(2)}份 ¥${Number(h.cost).toFixed(2)}`);
      });
      db.close();
    });
  });
});
