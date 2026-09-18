// 全量拉取基金历史净值（从成立日至今），用于区间涨跌幅（近1年/近3年/成立来）
// lsjz 接口单页最多 20 条；持仓基金优先
const DataFetcher = require('../data-fetcher');
const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('./fund_simulator.db');
const fetcher = new DataFetcher();
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const funds = await new Promise((res, rej) =>
    db.all('SELECT fund_code, inception_date FROM funds', [], (e, r) => e ? rej(e) : res(r)));
  const prio = ['005827', '161725', '000001', '005267'];
  funds.sort((a, b) => {
    const ia = prio.indexOf(a.fund_code), ib = prio.indexOf(b.fund_code);
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib) || a.fund_code.localeCompare(b.fund_code);
  });
  console.log('共', funds.length, '只基金，顺序:', funds.map(f => f.fund_code).join(','));
  for (const f of funds) {
    const start = f.inception_date || '2010-01-01';
    let all = [], page = 1, emptyPages = 0;
    while (page <= 300) {
      const batch = await fetcher.getNavHistory(f.fund_code, start, '', 20, page);
      if (!batch.length) { emptyPages++; if (emptyPages >= 2) break; page++; continue; }
      emptyPages = 0;
      all.push(...batch);
      if (batch.length < 20) break;
      page++;
      await sleep(180);
    }
    const map = new Map();
    for (const r of all) if (!map.has(r.nav_date)) map.set(r.nav_date, r);
    const merged = [...map.values()];
    let saved = 0;
    if (merged.length) saved = await fetcher.saveNavData(merged);
    const first = merged.length ? merged[merged.length - 1].nav_date : '-';
    const last = merged.length ? merged[0].nav_date : '-';
    console.log(`${f.fund_code} 拉取${all.length} 去重${merged.length} 入库${saved} 区间[${first} ~ ${last}]`);
    await sleep(200);
  }
  db.close();
  console.log('DONE');
})().catch(e => { console.error(e); db.close(); process.exit(1); });
