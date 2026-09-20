/**
 * 热点分析引擎：全市场基金按主题词聚类 → 板块平均日/周/月涨幅 → 热度分 + AI 点评
 * ctx: { db, userConfigs }
 */

const HOTSPOT_THEMES = [
  { key: '医药/医疗', kws: ['医药', '医疗', '生物', '健康', '创新药', '疫苗'] },
  { key: 'AI/科技', kws: ['人工智能', 'AI', '科技', '信息', '互联网', '软件', '计算机', '数字经济'] },
  { key: '白酒/消费', kws: ['白酒', '消费', '食品', '饮料', '啤酒', '乳业'] },
  { key: '半导体/芯片', kws: ['半导体', '芯片', '集成电路'] },
  { key: '新能源/光伏', kws: ['新能源', '光伏', '锂电', '电池', '碳中和', '储能', '风电'] },
  { key: '军工/国防', kws: ['军工', '国防', '航天', '卫星'] },
  { key: '港股/恒生', kws: ['港股', '恒生', '沪港深', 'H股'] },
  { key: '红利/价值', kws: ['红利', '价值', '低波', '沪深300'] },
  { key: '有色/资源', kws: ['有色', '资源', '矿业', '煤炭', '钢铁', '黄金'] },
  { key: '汽车/智能驾驶', kws: ['汽车', '智能驾驶', '自动驾驶'] },
  { key: '农业/养殖', kws: ['农业', '养殖', '农牧', '种业'] },
  { key: '地产/基建', kws: ['地产', '基建', '建筑', '建材'] },
  { key: '债券/固收', kws: ['债', '固收', '货币'] },
  { key: '量化/指数增强', kws: ['量化', '指数增强', '增强'] }
];

async function buildHotspots(ctx, userId) {
  const { db, userConfigs } = ctx;
  const all = (sql, params = []) => new Promise((resolve, reject) => db.all(sql, params, (e, r) => e ? reject(e) : resolve(r || [])));
  const rows = await all('SELECT fund_code, fund_name, day_return, r1w, r1m, scale FROM fund_universe');
  const agg = [];
  for (const t of HOTSPOT_THEMES) {
    const hits = rows.filter(r => t.kws.some(kw => (r.fund_name || '').includes(kw)) && r.day_return != null);
    if (hits.length < 3) continue;
    const n = hits.length;
    const avgDay = hits.reduce((s, r) => s + r.day_return, 0) / n;
    const wHits = hits.filter(r => r.r1w != null);
    const avgW = wHits.length ? wHits.reduce((s, r) => s + r.r1w, 0) / wHits.length : 0;
    const mHits = hits.filter(r => r.r1m != null);
    const avgM = mHits.length ? mHits.reduce((s, r) => s + r.r1m, 0) / mHits.length : 0;
    const hotScore = +(avgDay * 1 + avgW * 0.4).toFixed(2);
    agg.push({ theme: t.key, count: n, avg_day: +avgDay.toFixed(2), avg_week: +avgW.toFixed(2), avg_month: +avgM.toFixed(2), hot_score: hotScore, kws: t.kws });
  }
  agg.sort((a, b) => b.hot_score - a.hot_score);
  const top = agg.slice(0, 6);
  const watchCodes = new Set((await all('SELECT fund_code FROM watchlist WHERE user_id = ?', [userId])).map(r => r.fund_code));
  const holdCodes = new Set((await all('SELECT fund_code FROM holdings WHERE user_id = ?', [userId])).map(r => r.fund_code));
  for (const h of top) {
    const related = rows.filter(r => h.kws.some(kw => (r.fund_name || '').includes(kw)) &&
      (watchCodes.has(r.fund_code) || holdCodes.has(r.fund_code)));
    h.related = related.map(r => ({ fund_code: r.fund_code, fund_name: r.fund_name, day_return: r.day_return, watched: watchCodes.has(r.fund_code), held: holdCodes.has(r.fund_code) })).slice(0, 5);
  }
  const isAggressive = (userConfigs[userId] && userConfigs[userId].style === 'aggressive');
  const navDate = rows.filter(r => r.day_return != null).length ? '最新净值日' : '—';
  const hottest = top.find(h => h.hot_score > 0);
  let comment = '';
  let overall = '观望';
  if (!top.length) {
    comment = '当前基金库无明显热点板块，AI 维持防御，暂不追热点。';
    overall = '防御';
  } else if (hottest && hottest.avg_day >= 2.5) {
    overall = '热点爆发';
    comment = `${hottest.theme} 板块平均日涨幅 ${hottest.avg_day >= 0 ? '+' : ''}${hottest.avg_day}% 领涨全市场${isAggressive ? '，激进风格可关注相关基金轻仓介入，但注意不追高、等待回调企稳再加仓' : '，稳健风格暂不追高，等待回调确认后再评估'}`;
  } else if (hottest && hottest.avg_day >= 1) {
    overall = '热点启动';
    comment = `${hottest.theme} 板块 ${hottest.avg_day >= 0 ? '+' : ''}${hottest.avg_day}%（周 ${hottest.avg_week >= 0 ? '+' : ''}${hottest.avg_week}%）热点启动${isAggressive ? '，观察池相关基金若出现 BUY 信号可分批介入' : '，先观察持续性，确认不一日游再考虑'}`;
  } else if (hottest && hottest.avg_day > 0) {
    overall = '温和走强';
    comment = `${hottest.theme} 温和走强（日 ${hottest.avg_day >= 0 ? '+' : ''}${hottest.avg_day}%），暂未形成趋势性热点，AI 继续持有跟踪。`;
  } else {
    overall = '热点退潮';
    comment = '当日全市场板块普遍回调，无强势热点，AI 以控制回撤为主，不追跌。';
  }
  return { nav_date: navDate, generated_at: new Date().toISOString(), overall, comment, hotspots: top, user_style: isAggressive ? 'aggressive' : 'default' };
}

module.exports = { buildHotspots, HOTSPOT_THEMES };
