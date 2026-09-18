# -*- coding: utf-8 -*-
"""server.js 新增 AI 热点关注与分析：
①引擎 buildHotspots(userId)：主题词聚类全市场基金涨幅 → 热点板块 + 热度分 + AI 点评（按性格）+ 观察池关联
②API /api/ai/hotspots
③close 分析后自动跑热点分析并写 analysis_logs(type=hotspot)"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) 热点引擎 + API（插在 /api/ai/fund-fees 后）
anchor = """// 用户管理API
app.get('/api/users', async (req, res) => {"""
api = """// ===== AI 市场热点关注与分析（主题词聚类全市场 → 热点板块 + AI 点评 + 观察池关联）=====
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

// 热点引擎：全市场基金按主题词聚类 → 板块平均日/周/月涨幅 → 热度分 + AI 点评（按用户性格）
async function buildHotspots(userId) {
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
    // 热度分：日动能为主、周动能辅
    const hotScore = +(avgDay * 1 + avgW * 0.4).toFixed(2);
    agg.push({ theme: t.key, count: n, avg_day: +avgDay.toFixed(2), avg_week: +avgW.toFixed(2), avg_month: +avgM.toFixed(2), hot_score: hotScore, kws: t.kws });
  }
  agg.sort((a, b) => b.hot_score - a.hot_score);
  const top = agg.slice(0, 6);

  // 观察池关联：热点板块内该用户已观察/持仓的基金
  const watchCodes = new Set((await all('SELECT fund_code FROM watchlist WHERE user_id = ?', [userId])).map(r => r.fund_code));
  const holdCodes = new Set((await all('SELECT fund_code FROM holdings WHERE user_id = ?', [userId])).map(r => r.fund_code));
  for (const h of top) {
    const related = rows.filter(r => h.kws.some(kw => (r.fund_name || '').includes(kw)) &&
      (watchCodes.has(r.fund_code) || holdCodes.has(r.fund_code)));
    h.related = related.map(r => ({ fund_code: r.fund_code, fund_name: r.fund_name, day_return: r.day_return, watched: watchCodes.has(r.fund_code), held: holdCodes.has(r.fund_code) })).slice(0, 5);
  }

  // AI 点评（规则引擎，按用户性格）
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

  const result = { nav_date: navDate, generated_at: new Date().toISOString(), overall, comment, hotspots: top, user_style: isAggressive ? 'aggressive' : 'default' };
  return result;
}

app.get('/api/ai/hotspots', async (req, res) => {
  try {
    const userId = req.query.user_id || currentUser;
    if (!userConfigs[userId]) return res.status(404).json({ error: '用户不存在' });
    const data = await buildHotspots(userId);
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 用户管理API
app.get('/api/users', async (req, res) => {"""
assert s.count(anchor) == 1, 'anchor not found'
s = s.replace(anchor, api)

# 2) close 分析后自动跑热点分析（写 analysis_logs type=hotspot）
old2 = """    // 收盘分析后保存当日账户快照（用于资产走势/每日盈亏真实图表）
    if (analysisType === 'close') {"""
new2 = """    // 收盘后：AI 市场热点关注与分析（每用户独立点评，写 analysis_logs type=hotspot）
    if (analysisType === 'close') {
      for (const userId of Object.keys(userConfigs)) {
        try {
          const hp = await buildHotspots(userId);
          await new Promise((resolve) => {
            db.run('INSERT INTO analysis_logs (user_id, analysis_type, fund_code, decision, confidence, entry_price, target_price, stop_loss, analysis_time, current_nav, daily_return, estimated_close_return, estimated_pnl, signal_label, signal_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
              [userId, 'hotspot', 'HOTSPOT', hp.overall, hp.hot_score || 0, 0, 0, 0, new Date().toISOString(), 0, 0, 0, 0, hp.hottest_theme || (hp.hotspots[0] && hp.hotspots[0].theme) || '', hp.comment], (err) => resolve());
          });
          console.log(`[热点] ${userId} AI 热点分析：${hp.overall}（${hp.hotspots.map(h => h.theme + ' ' + h.avg_day + '%').slice(0, 3).join(' / ')}）${hp.comment.slice(0, 40)}`);
        } catch (hpErr) {
          console.error(`[热点] ${userId} 热点分析失败:`, hpErr.message);
        }
      }
    }

    // 收盘分析后保存当日账户快照（用于资产走势/每日盈亏真实图表）
    if (analysisType === 'close') {"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('server.js hotspots patched')
