const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('fund_simulator.db');
const THEME_RE = /新能源|白酒|能源|成长|消费|科技|军工|医药|互联网|半导体|芯片|集成电路|数字|人工智能|创新|制造|改革|新兴|软件|传媒|游戏|化工|有色|农业|电子|通信|计算机|机器人|高端装备|主题/;
db.all("SELECT fund_code, fund_name, fund_type, unit_nav, day_return, r1m, r3m, r6m, r1y, inception_date, scale FROM fund_universe", (err, universe) => {
  if (err) { console.log('ERR', err.message); return; }
  const candidates = [];
  for (const f of universe) {
    if (!f.unit_nav || f.unit_nav <= 0) continue;
    if (f.scale != null && f.scale < 2) continue;
    if (f.inception_date && f.inception_date > '2025-09-18') continue;
    const theme = THEME_RE.test(f.fund_name || '');
    if ((f.fund_type !== '指数型' && f.fund_type !== '混合型') || theme) continue;
    const r1y = f.r1y != null ? f.r1y : 0;
    const r3m = f.r3m != null ? f.r3m : 0;
    const r6m = f.r6m != null ? f.r6m : 0;
    const day = f.day_return != null ? f.day_return : 0;
    const score = Math.max(r1y, 0) * 0.5 + Math.max(r6m, 0) * 0.3 + Math.max(day, 0) * 0.3
      + (r3m >= 0 ? 1.0 : 0) + (r6m < -15 ? -4 : 0) + (f.fund_type === '指数型' ? 6 : 0);
    candidates.push({ code: f.fund_code, name: f.fund_name, type: f.fund_type, score: Number(score.toFixed(2)), r1y, r6m, day, scale: f.scale });
  }
  candidates.sort((a, b) => b.score - a.score);
  console.log('稳健候选总数:', candidates.length);
  console.log('TOP 25:');
  candidates.slice(0, 25).forEach((c, i) => {
    console.log(String(i + 1).padStart(2), c.code, c.name, '[' + c.type + ']', 'score=' + c.score, 'r1y=' + c.r1y, 'r6m=' + c.r6m, 'scale=' + (c.scale == null ? '-' : c.scale));
  });
});
