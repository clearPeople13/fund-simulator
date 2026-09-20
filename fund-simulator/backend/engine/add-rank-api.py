# -*- coding: utf-8 -*-
"""routes.js 新增 GET /funds/:code/rank（同类排名百分位：近1月/近3月/近6月/近1年）"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'api', 'routes.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """// 获取基金净值历史
router.get('/funds/:code/nav', async (req, res) => {"""
# 注意：dividends 端点已在此锚点前插入，此处锚点仍唯一（nav 注释）
new = """// 同类排名（全市场基金库同类型基金区间涨幅百分位）
router.get('/funds/:code/rank', (req, res) => {
  const { code } = req.params;
  const fieldMap = { r1m: 'r1m', r3m: 'r3m', r6m: 'r6m', r1y: 'r1y' };
  const labelMap = { r1m: '近1月', r3m: '近3月', r6m: '近6月', r1y: '近1年' };
  db.get('SELECT fund_type FROM fund_universe WHERE fund_code = ?', [code], (err, f) => {
    if (err) { res.status(500).json({ error: err.message }); return; }
    if (!f || !f.fund_type) { res.json({ fund_code: code, found: false }); return; }
    const peers = (sql, field, cb) => {
      db.all(`SELECT fund_code, ${field} AS v FROM fund_universe WHERE fund_type = ? AND ${field} IS NOT NULL`, [f.fund_type], (e, rows) => cb(e, rows));
    };
    const result = { fund_code: code, found: true, fund_type: f.fund_type, ranks: [] };
    const keys = ['r1m', 'r3m', 'r6m', 'r1y'];
    let pending = keys.length;
    keys.forEach(k => {
      peers(null, k, (e, rows) => {
        if (e) { pending = 0; res.status(500).json({ error: e.message }); return; }
        const sorted = [...rows].sort((a, b) => (b.v || -999) - (a.v || -999));
        const total = sorted.length;
        const idx = sorted.findIndex(r => r.fund_code === code);
        const pct = idx >= 0 ? Math.round((idx / total) * 100) : null;
        result.ranks.push({ key: k, label: labelMap[k], rank: idx >= 0 ? idx + 1 : null, total, percentile: pct, value: idx >= 0 ? sorted[idx].v : null });
        if (--pending === 0) res.json(result);
      });
    });
  });
});

// 获取基金净值历史
router.get('/funds/:code/nav', async (req, res) => {"""
assert s.count(old) == 1, 'anchor not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('rank api added')
