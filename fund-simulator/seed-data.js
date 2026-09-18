/**
 * 基金数据种子脚本
 * 从天天基金网拉取精选基金的真实净值数据并入库（可重复执行，幂等）
 * 用法: node seed-data.js
 */
const FundDataFetcher = require('./data-fetcher.js');

// 精选基金（覆盖 混合/股票/指数/债券/QDII，与前端 mock、用户配置关注列表对齐）
const SEED_CODES = [
  '110011', '161725', '005827', '003834', '005267', // 默认用户持仓/关注
  '260108', '320007', '001156', '001938', '519736', // 激进用户持仓/关注
  '000961', '000001', '000011', '000041', '001015', '002001', '002011' // 观察池
];

// 拉取窗口：近 180 天
function calcDateRange(days) {
  const end = new Date();
  const start = new Date(end.getTime() - days * 24 * 60 * 60 * 1000);
  const fmt = d => d.toISOString().split('T')[0];
  return { startDate: fmt(start), endDate: fmt(end) };
}

async function main() {
  const fetcher = new FundDataFetcher();
  const { startDate, endDate } = calcDateRange(180);
  console.log(`窗口: ${startDate} ~ ${endDate}\n`);

  // 1. 拉取全量基金列表，建立 代码 → {名称, 类型} 映射
  console.log('=== 1/3 拉取基金列表 ===');
  const fundList = await fetcher.getFundList();
  const infoMap = new Map(fundList.map(f => [f.fund_code, f]));
  console.log(`基金代码库 ${fundList.length} 条`);

  // 2. 写入 funds 表
  console.log('\n=== 2/3 写入基金信息 ===');
  let savedFunds = 0;
  for (const code of SEED_CODES) {
    const info = infoMap.get(code);
    if (!info) { console.log(`✗ ${code} 不在代码库中，跳过`); continue; }
    await fetcher.saveFundInfo({
      fund_code: code,
      fund_name: info.fund_name,
      fund_type: info.fund_type
    });
    savedFunds++;
    console.log(`✓ ${code} ${info.fund_name} [${info.fund_type}]`);
  }

  // 3. 拉取历史净值并入库
  console.log('\n=== 3/3 拉取历史净值（近180天） ===');
  const summary = [];
  for (const code of SEED_CODES) {
    const info = infoMap.get(code);
    const navList = await fetcher.getNavHistoryAll(code, startDate, endDate, 12);
    let inserted = 0;
    if (navList.length > 0) {
      inserted = await fetcher.saveNavData(navList);
    }
    summary.push({ code, name: info ? info.fund_name : code, fetched: navList.length, inserted });
    console.log(`${navList.length > 0 ? '✓' : '✗'} ${code} ${(info ? info.fund_name : '').padEnd(14)} 拉取 ${String(navList.length).padStart(3)} 条, 新增 ${String(inserted).padStart(3)} 条` +
      (navList[0] ? `, 最新 ${navList[0].nav_date} 净值 ${navList[0].unit_nav}` : ''));
    await new Promise(resolve => setTimeout(resolve, 300));
  }

  fetcher.close();

  console.log('\n=== 汇总 ===');
  console.log(`基金信息入库 ${savedFunds} 只，净值数据 ${summary.reduce((s, x) => s + x.inserted, 0)} 条`);
}

main().catch(e => { console.error('种子脚本失败:', e); process.exit(1); });
