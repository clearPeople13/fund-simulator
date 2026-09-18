const path = require('path');
const sqlite3 = require(path.join(process.cwd(), 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');

// 主题关键词映射（基金名称匹配）
const THEMES = [
  { key: '白酒/消费', kws: ['白酒', '消费', '食品', '饮料', '啤酒', '乳业'] },
  { key: '医药/医疗', kws: ['医药', '医疗', '生物', '健康', '创新药', '疫苗'] },
  { key: 'AI/科技', kws: ['人工智能', 'AI', '科技', '信息', '互联网', '软件', '计算机', '数字经济'] },
  { key: '半导体/芯片', kws: ['半导体', '芯片', '集成电路'] },
  { key: '新能源/光伏', kws: ['新能源', '光伏', '锂电', '电池', '碳中和', '储能', '风电'] },
  { key: '军工/国防', kws: ['军工', '国防', '航天', '卫星'] },
  { key: '港股/恒生', kws: ['港股', '恒生', '沪港深', 'H股'] },
  { key: '红利/价值', kws: ['红利', '价值', '低波', '沪深300'] },
  { key: '有色/资源', kws: ['有色', '资源', '矿业', '煤炭', '钢铁', '黄金'] },
  { key: '地产/基建', kws: ['地产', '基建', '建筑', '建材'] },
  { key: '债券/固收', kws: ['债', '固收', '货币'] },
  { key: '量化/指数增强', kws: ['量化', '指数增强', '增强'] },
  { key: '汽车/智能驾驶', kws: ['汽车', '智能驾驶', '自动驾驶'] },
  { key: '农业/养殖', kws: ['农业', '养殖', '农牧', '种业'] },
];

db.all('SELECT fund_code, fund_name, day_return, r1w, r1m, scale FROM fund_universe', (e, rows) => {
  if (e) { console.error(e.message); process.exit(1); }
  const agg = {};
  for (const t of THEMES) {
    const hits = rows.filter(r => t.kws.some(kw => (r.fund_name || '').includes(kw)) && r.day_return != null);
    if (!hits.length) continue;
    const avgDay = hits.reduce((s, r) => s + r.day_return, 0) / hits.length;
    const avgW = hits.filter(r => r.r1w != null).reduce((s, r) => s + r.r1w, 0) / Math.max(1, hits.filter(r => r.r1w != null).length);
    const avgM = hits.filter(r => r.r1m != null).reduce((s, r) => s + r.r1m, 0) / Math.max(1, hits.filter(r => r.r1m != null).length);
    agg[t.key] = { count: hits.length, avgDay: +avgDay.toFixed(2), avgW: +avgW.toFixed(2), avgM: +avgM.toFixed(2) };
  }
  const sorted = Object.entries(agg).sort((a, b) => b[1].avgDay - a[1].avgDay);
  console.log('=== 当日热点板块（按平均日涨幅）===');
  sorted.slice(0, 10).forEach(([k, v]) => console.log(`${k.padEnd(10)} 基金${String(v.count).padStart(4)} 日${v.avgDay >= 0 ? '+' : ''}${v.avgDay}% 周${v.avgW >= 0 ? '+' : ''}${v.avgW}% 月${v.avgM >= 0 ? '+' : ''}${v.avgM}%`));
  db.close();
});
