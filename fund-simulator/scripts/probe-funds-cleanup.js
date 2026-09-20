// 探查：funds 表所有基金及其被引用情况（watchlist/holdings/orders/transactions/fund_fees）
const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');

db.serialize(() => {
  db.all(`SELECT fund_code, fund_name, fund_type FROM funds ORDER BY fund_code`, (err, funds) => {
    if (err) { console.error(err.message); process.exit(1); }
    console.log('funds 总数:', funds.length);
    const queries = [
      ['watchlist', 'SELECT DISTINCT fund_code FROM watchlist'],
      ['holdings', 'SELECT DISTINCT fund_code FROM holdings'],
      ['orders', 'SELECT DISTINCT fund_code FROM orders'],
      ['transactions', 'SELECT DISTINCT fund_code FROM transactions'],
      ['fund_fees', 'SELECT DISTINCT fund_code FROM fund_fees'],
    ];
    const results = {};
    let remaining = queries.length;
    queries.forEach(([name, sql]) => {
      db.all(sql, (e, rows) => {
        results[name] = e ? [] : rows.map(r => r.fund_code);
        remaining--;
        if (remaining === 0) {
          const referenced = new Set();
          queries.forEach(([n]) => (results[n] || []).forEach(c => referenced.add(c)));
          console.log('引用集合:', [...referenced].sort().join(', '));
          console.log('引用基金数:', referenced.size);
          console.log('\n=== 无任何引用的 funds（可清理候选） ===');
          const orphan = funds.filter(f => !referenced.has(f.fund_code));
          orphan.forEach(f => console.log(`${f.fund_code} | ${f.fund_name} | ${f.fund_type}`));
          console.log('\n可清理候选数:', orphan.length);
          // watchlist 手动源明细（保留依据）
          db.all(`SELECT fund_code, source FROM watchlist`, (e2, wrows) => {
            console.log('\nwatchlist 明细（source）:');
            (wrows || []).forEach(r => console.log(`  ${r.fund_code} ${r.source}`));
            db.close();
          });
        }
      });
    });
  });
});
