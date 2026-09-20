const path = require('path');
const sqlite3 = require(path.join(process.cwd(), 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
const q = (sql, p = []) => new Promise((res, rej) => db.all(sql, p, (e, r) => e ? rej(e) : res(r || [])));
(async () => {
  try {
    // 清空重推（排除复权型）
    await new Promise((res, rej) => db.run('DELETE FROM dividends', e => e ? rej(e) : res()));
    const codes = await q('SELECT DISTINCT fund_code FROM fund_nav');
    let total = 0, funds = 0, skipped = 0;
    for (const { fund_code: code } of codes) {
      const rows = await q('SELECT nav_date, unit_nav, acc_nav FROM fund_nav WHERE fund_code = ? AND acc_nav IS NOT NULL AND acc_nav > 0 ORDER BY nav_date', [code]);
      if (!rows.length) continue;
      let prevCum = null, jumps = [];
      for (const row of rows) {
        const cum = +(row.acc_nav - row.unit_nav).toFixed(4);
        if (prevCum != null && Math.abs(cum - prevCum) > 0.0001) {
          jumps.push({ date: row.nav_date, per_unit: +(cum - prevCum).toFixed(4) });
        }
        prevCum = cum;
      }
      // 过滤：只保留正跳变（分红）；跳变密度 >20% 视为复权累计净值型（每日复权，非分红）
      const density = rows.length ? jumps.length / rows.length : 0;
      if (density > 0.2) { skipped++; console.log(code, '跳过（复权型，密度', density.toFixed(2) + '）'); continue; }
      const pos = jumps.filter(j => j.per_unit > 0);
      if (!pos.length) continue;
      for (const j of pos) {
        await new Promise((res, rej) => db.run('INSERT OR IGNORE INTO dividends (fund_code, ex_date, per_unit, type) VALUES (?, ?, ?, ?)',
          [code, j.date, j.per_unit, 'CASH'], e => e ? rej(e) : res()));
      }
      total += pos.length; funds++;
      console.log(code, '→', pos.length, '次分红（最近:', pos[pos.length - 1].date, '+' + pos[pos.length - 1].per_unit + '）');
    }
    console.log('=== 完成：', funds, '只基金', total, '条分红；跳过复权型', skipped, '只 ===');
    db.close();
  } catch (e) { console.error('FAIL:', e.message); process.exit(1); }
})();
