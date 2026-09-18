// 全市场基金库同步：天天基金 rankhandler 排行接口（股票型/混合型/指数型/QDII）
// 用法: node engine/sync-fund-universe.js
const axios = require('axios');
const sqlite3 = require('sqlite3');
const path = require('path');

const dbPath = path.join(__dirname, '..', 'fund_simulator.db');
const db = new sqlite3.Database(dbPath);

const TYPES = [
  { ft: 'gp', label: '股票型' },
  { ft: 'hh', label: '混合型' },
  { ft: 'zs', label: '指数型' },
  { ft: 'qdii', label: 'QDII' }
];

function run(sql, params) {
  return new Promise((resolve, reject) => {
    db.run(sql, params, function (err) { err ? reject(err) : resolve(this.changes); });
  });
}

async function fetchPage(ft, pi, pn) {
  const url = `https://fund.eastmoney.com/data/rankhandler.aspx?op=ph&dt=kf&ft=${ft}&rs=&gs=0&sc=1nzf&st=desc&pi=${pi}&pn=${pn}&dx=1&v=${Math.random()}`;
  const resp = await axios.get(url, {
    headers: { 'Referer': 'https://fund.eastmoney.com/data/fundranking.html', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36' },
    timeout: 20000
  });
  const text = String(resp.data);
  const m = text.match(/var rankData = (\{.*\})\s*;?\s*$/s);
  if (!m) throw new Error('parse fail, len=' + text.length + ' head=' + text.slice(0, 80));
  // rankhandler 返回非严格 JSON（键无引号），先补引号再解析
  const fixed = m[1].replace(/([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:/g, '$1"$2":');
  return JSON.parse(fixed);
}

(async () => {
  await run(`CREATE TABLE IF NOT EXISTS fund_universe (
    fund_code TEXT PRIMARY KEY,
    fund_name TEXT,
    fund_type TEXT,
    nav_date TEXT,
    unit_nav REAL,
    day_return REAL,
    r1w REAL, r1m REAL, r3m REAL, r6m REAL, r1y REAL, r2y REAL, r3y REAL, ytd REAL, since REAL,
    inception_date TEXT,
    scale REAL,
    updated_at TEXT
  )`);

  let totalAll = 0;
  for (const t of TYPES) {
    const first = await fetchPage(t.ft, 1, 50);
    const total = Number(first.allRecords || first.AllRecords || 0) || 0;
    const pages = Math.ceil(total / 50);
    console.log(`${t.label}: total=${total}, pages=${pages}`);
    let saved = 0;
    for (let pi = 1; pi <= pages; pi++) {
      let data;
      try {
        data = await fetchPage(t.ft, pi, 50);
      } catch (e) {
        console.log(`  page ${pi} fail: ${e.message}, retry once`);
        await new Promise(r => setTimeout(r, 2000));
        try { data = await fetchPage(t.ft, pi, 50); } catch (e2) { console.log(`  page ${pi} skip`); continue; }
      }
      const rows = (data.datas || []).filter(Boolean);
      for (const line of rows) {
        const f = String(line).split(',');
        if (f.length < 25) continue;
        const code = f[0];
        const name = f[1];
        const navDate = f[3] || '';
        const nav = parseFloat(f[4]) || 0;
        const dayRet = parseFloat(f[6]);
        const r1w = parseFloat(f[7]), r1m = parseFloat(f[8]), r3m = parseFloat(f[9]), r6m = parseFloat(f[10]);
        const r1y = parseFloat(f[11]), r2y = parseFloat(f[12]), r3y = parseFloat(f[13]);
        const ytd = parseFloat(f[14]), since = parseFloat(f[15]);
        const inception = f[16] || '';
        const scale = parseFloat(f[24]);
        await run(`INSERT OR REPLACE INTO fund_universe
          (fund_code, fund_name, fund_type, nav_date, unit_nav, day_return, r1w, r1m, r3m, r6m, r1y, r2y, r3y, ytd, since, inception_date, scale, updated_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now','localtime'))`,
          [code, name, t.label, navDate, nav, isNaN(dayRet) ? null : dayRet, isNaN(r1w) ? null : r1w, isNaN(r1m) ? null : r1m,
           isNaN(r3m) ? null : r3m, isNaN(r6m) ? null : r6m, isNaN(r1y) ? null : r1y, isNaN(r2y) ? null : r2y,
           isNaN(r3y) ? null : r3y, isNaN(ytd) ? null : ytd, isNaN(since) ? null : since, inception, isNaN(scale) ? null : scale]);
        saved++;
      }
      if (pi % 20 === 0 || pi === pages) console.log(`  ${t.label} ${pi}/${pages} 页, 已存 ${saved}`);
      await new Promise(r => setTimeout(r, 300));
    }
    totalAll += saved;
    console.log(`${t.label} 完成，共 ${saved} 只`);
  }
  db.all('SELECT COUNT(*) n, COUNT(DISTINCT fund_type) t FROM fund_universe', (e, r) => {
    console.log('FINAL:', JSON.stringify(r));
  });
  setTimeout(() => process.exit(0), 500);
})();
