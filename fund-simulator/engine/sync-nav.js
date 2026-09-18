/**
 * 净值增量同步脚本：从天天基金拉取最近净值并入库
 * 用法: node engine/sync-nav.js [startDate]
 */
const path = require('path');
process.chdir(path.join(__dirname, '..'));
const FundDataFetcher = require('../data-fetcher');
const sqlite3 = require('sqlite3').verbose();

const fetcher = new FundDataFetcher();
const startDate = process.argv[2] || '2026-09-10';
// endDate 必须留空：天天基金接口传当天/未来日期会返回空；startDate 需横线格式 YYYY-MM-DD
const endDate = '';

function getFunds() {
  return new Promise((resolve, reject) => {
    fetcher.db.all('SELECT fund_code, fund_name FROM funds ORDER BY fund_code', (err, rows) => err ? reject(err) : resolve(rows));
  });
}

async function main() {
  const funds = await getFunds();
  console.log(`共 ${funds.length} 只基金，同步区间 ${startDate} ~ ${endDate}`);
  let totalInserted = 0;
  const results = [];
  for (const f of funds) {
    try {
      const navList = await fetcher.getNavHistoryAll(f.fund_code, startDate, endDate, 5);
      let inserted = 0;
      if (navList.length > 0) inserted = await fetcher.saveNavData(navList);
      totalInserted += inserted;
      const latest = navList[0] ? `${navList[0].nav_date} nav=${navList[0].unit_nav} ${navList[0].daily_return}%` : '无新数据';
      results.push(`${f.fund_code} ${f.fund_name}: 拉到 ${navList.length} 条, 新入库 ${inserted}, 最新: ${latest}`);
      await new Promise(r => setTimeout(r, 250));
    } catch (e) {
      results.push(`${f.fund_code} 失败: ${e.message}`);
    }
  }
  console.log(results.join('\n'));
  console.log(`\n总计新入库 ${totalInserted} 条`);
  fetcher.close();
}

main().catch(e => { console.error(e); process.exit(1); });
