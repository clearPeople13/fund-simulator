# -*- coding: utf-8 -*-
"""routes.js 新增 GET /funds/:code/dividends（历史分红明细）"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'api', 'routes.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """// 获取基金净值历史
router.get('/funds/:code/nav', async (req, res) => {"""
new = """// 历史分红明细（由累计净值-单位净值跳变推导，dividends 表）
router.get('/funds/:code/dividends', (req, res) => {
  const { code } = req.params;
  const limit = Math.min(parseInt(req.query.limit || '20', 10) || 20, 200);
  db.all('SELECT ex_date, per_unit, type FROM dividends WHERE fund_code = ? ORDER BY ex_date DESC LIMIT ?', [code, limit], (err, rows) => {
    if (err) { res.status(500).json({ error: err.message }); return; }
    db.get('SELECT COUNT(*) AS total FROM dividends WHERE fund_code = ?', [code], (err2, cnt) => {
      if (err2) { res.status(500).json({ error: err2.message }); return; }
      res.json({ fund_code: code, total: cnt ? cnt.total : 0, list: rows || [] });
    });
  });
});

// 获取基金净值历史
router.get('/funds/:code/nav', async (req, res) => {"""
assert s.count(old) == 1, 'anchor not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('routes.js dividends endpoint added')
