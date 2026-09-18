// 清理 funds 表无引用孤儿基金（不在 watchlist/holdings/orders/transactions/fund_fees 的行）
// 只删 funds 行；fund_nav 真实净值历史保留（未来重新入库可直接复用，不破坏数据）
const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');

db.serialize(() => {
  db.all('SELECT DISTINCT fund_code FROM watchlist', (e1, w) => {
    db.all('SELECT DISTINCT fund_code FROM holdings', (e2, h) => {
      db.all('SELECT DISTINCT fund_code FROM orders', (e3, o) => {
        db.all('SELECT DISTINCT fund_code FROM transactions', (e4, t) => {
          db.all('SELECT DISTINCT fund_code FROM fund_fees', (e5, f) => {
            const ref = new Set();
            [w, h, o, t, f].forEach(rows => (rows || []).forEach(r => ref.add(r.fund_code)));
            db.all('SELECT fund_code, fund_name FROM funds ORDER BY fund_code', (e6, funds) => {
              const orphans = funds.filter(x => !ref.has(x.fund_code));
              console.log('引用基金:', ref.size, '| funds 总数:', funds.length, '| 待清理孤儿:', orphans.length);
              const codes = orphans.map(x => x.fund_code);
              const placeholders = codes.map(() => '?').join(',');
              db.run(`DELETE FROM funds WHERE fund_code IN (${placeholders})`, codes, function (err) {
                if (err) { console.error('DELETE 失败:', err.message); process.exit(1); }
                console.log(`已删除 funds 孤儿 ${this.changes} 行`);
                db.all('SELECT COUNT(*) c FROM funds', (e7, r1) => {
                  console.log('清理后 funds 总数:', r1[0].c);
                  db.all(`SELECT COUNT(*) c FROM fund_nav WHERE fund_code IN (${placeholders})`, codes, (e8, r2) => {
                    console.log('保留的孤儿基金净值历史条数（不删除）:', r2[0].c);
                    db.all('SELECT COUNT(*) c FROM watchlist', (e9, r3) => {
                      db.all('SELECT COUNT(*) c FROM holdings', (e10, r4) => {
                        db.all('SELECT COUNT(*) c FROM orders', (e11, r5) => {
                          console.log('联动检查 → watchlist:', r3[0].c, '| holdings:', r4[0].c, '| orders:', r5[0].c);
                          console.log('清理明细:');
                          orphans.forEach(x => console.log(`  DEL ${x.fund_code} ${x.fund_name}`));
                          db.close();
                        });
                      });
                    });
                  });
                });
              });
            });
          });
        });
      });
    });
  });
});
