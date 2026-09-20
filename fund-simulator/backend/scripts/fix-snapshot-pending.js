// 按新口径重算 9/18 快照（待确认持仓按成本），9/17 不动
const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
const all = (sql, args) => new Promise((res, rej) => db.all(sql, args, (e, r) => e ? rej(e) : res(r)));
const one = (sql, args) => new Promise((res, rej) => db.get(sql, args, (e, r) => e ? rej(e) : res(r)));
const run = (sql, args) => new Promise((res, rej) => db.run(sql, args, function(e) { e ? rej(e) : res(this); }));

(async () => {
  for (const uid of ['default', 'aggressive']) {
    const holdings = await all('SELECT fund_code, shares, total_cost FROM holdings WHERE user_id=?', [uid]);
    let mv = 0;
    for (const h of holdings) {
      // 当日买入（9/18）→ 按成本；否则按最新净值（9/17）
      const lastBuy = await one("SELECT transaction_date FROM transactions WHERE user_id=? AND fund_code=? AND transaction_type='BUY' ORDER BY transaction_date DESC LIMIT 1", [uid, h.fund_code]);
      const isToday = lastBuy && lastBuy.transaction_date && lastBuy.transaction_date.slice(0, 10) === '2026-09-18';
      if (isToday) {
        mv += h.total_cost;
      } else {
        const nav = await one("SELECT unit_nav FROM fund_nav WHERE fund_code=? ORDER BY nav_date DESC LIMIT 1", [h.fund_code]);
        mv += nav ? h.shares * nav.unit_nav : h.total_cost;
      }
    }
    const pd = await one('SELECT cash, total_assets FROM portfolio_daily WHERE user_id=? AND date=?', [uid, '2026-09-17']);
    const cash = await one('SELECT cash FROM portfolio_daily WHERE user_id=? AND date=?', [uid, '2026-09-18']);
    const total = cash.cash + mv;
    const pnl = total - pd.total_assets;
    await run('UPDATE portfolio_daily SET total_assets=?, daily_pnl=?, market_value=? WHERE user_id=? AND date=?', [total, pnl, mv, uid, '2026-09-18']);
    console.log(`${uid}: 9/18 total=${total.toFixed(2)} pnl=${pnl.toFixed(2)} mv=${mv.toFixed(2)} 累计=${(total-100000).toFixed(2)}`);
  }
  db.close();
})().catch(e => { console.error(e); db.close(); });
