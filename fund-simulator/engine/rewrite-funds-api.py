# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\api\routes.js'
c = io.open(p, encoding='utf-8').read()

# 1. GET /funds（全市场基金库）——替换到 GET /funds/:code 之前
start_marker = "// 获取基金列表"
i0 = c.index(start_marker)
i1 = c.index("router.get('/funds/:code', (req, res) => {")
new_list = """// 获取基金列表（全市场基金库 fund_universe，与 AI 观察池/持仓独立）
router.get('/funds', (req, res) => {
  const { type, sort, order, page = 1, limit = 20, keyword } = req.query;

  const where = [];
  const params = [];
  if (type) {
    where.push('u.fund_type = ?');
    params.push(type);
  }
  if (keyword) {
    const kw = '%' + String(keyword) + '%';
    where.push('(u.fund_code LIKE ? OR u.fund_name LIKE ?)');
    params.push(kw, kw);
  }
  const whereSql = where.length ? ' WHERE ' + where.join(' AND ') : '';

  // 排序白名单：支持按涨幅/净值/代码排序
  const sortMap = {
    fund_code: 'u.fund_code', fund_name: 'u.fund_name',
    day_return: 'u.day_return', r1m: 'u.r1m', r3m: 'u.r3m', r6m: 'u.r6m', r1y: 'u.r1y',
    unit_nav: 'u.unit_nav', scale: 'u.scale'
  };
  const sortCol = sortMap[sort] || 'u.r6m';
  const sortDir = order === 'asc' ? 'ASC' : 'DESC';

  const offset = (parseInt(page) - 1) * parseInt(limit);
  const query = `SELECT u.fund_code, u.fund_name, u.fund_type, u.unit_nav AS latest_nav, u.nav_date AS latest_nav_date,
        u.day_return, u.r6m AS recent_return, u.inception_date, u.scale
      FROM fund_universe u${whereSql}
      ORDER BY ${sortCol} ${sortDir} LIMIT ? OFFSET ?`;
  params.push(parseInt(limit), offset);

  db.all(query, params, (err, rows) => {
    if (err) { res.status(500).json({ error: err.message }); return; }
    const countQuery = `SELECT COUNT(*) AS total FROM fund_universe u${whereSql}`;
    db.get(countQuery, where.length ? params.slice(0, params.length - 2) : [], (err2, countRow) => {
      if (err2) { res.status(500).json({ error: err2.message }); return; }
      res.json({
        data: rows,
        pagination: { page: parseInt(page), limit: parseInt(limit), total: countRow.total }
      });
    });
  });
});

"""
c = c[:i0] + new_list + c[i1:]

# 2. GET /funds/:code 兼容 universe
i2 = c.index("router.get('/funds/:code', (req, res) => {")
j2 = c.index("// 获取基金净值历史", i2)
new_detail = """router.get('/funds/:code', (req, res) => {
  const { code } = req.params;

  db.get('SELECT * FROM funds WHERE fund_code = ?', [code], (err, row) => {
    if (err) { res.status(500).json({ error: err.message }); return; }
    if (row) { res.json(row); return; }

    // 全市场基金库兜底：未纳入跟踪的新基金也返回基础信息
    db.get('SELECT fund_code, fund_name, fund_type, unit_nav AS latest_nav, nav_date AS latest_nav_date, day_return, r6m AS recent_return, inception_date, scale FROM fund_universe WHERE fund_code = ?', [code], (err2, urow) => {
      if (err2) { res.status(500).json({ error: err2.message }); return; }
      if (!urow) { res.status(404).json({ error: '基金不存在' }); return; }
      res.json({ ...urow, tracked: false });
    });
  });
});

"""
c = c[:i2] + new_detail + c[j2:]

io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
