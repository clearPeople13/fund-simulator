/**
 * 只读查询路由：/api/reports /api/funds /api/alerts /api/market-env /api/risk /api/orders /api/audit /api/benchmark /api/performance
 * ctx: { db, getCurrentUser, getRiskParams }
 */
const { Router } = require('express');

module.exports = function readonlyRoutes(ctx) {
  const r = Router();
  const { db, getCurrentUser, getRiskParams } = ctx;

  r.get('/reports', async (req, res) => {
    try {
      const userId = req.query.user_id || getCurrentUser();
      const type = req.query.type || 'weekly';
      const rows = await new Promise((resolve, reject) => {
        db.all('SELECT * FROM reports WHERE user_id = ? AND report_type = ? ORDER BY id DESC LIMIT 10', [userId, type], (e, rows) => e ? reject(e) : resolve(rows || []));
      });
      res.json({ user_id: userId, reports: rows });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.get('/reports/:id', (req, res) => {
    db.get('SELECT * FROM reports WHERE id = ?', [req.params.id], (e, row) => {
      if (e) return res.status(500).json({ error: e.message });
      if (!row) return res.status(404).json({ error: '报告不存在' });
      res.json({ report: row });
    });
  });

  r.get('/market/overview', async (req, res) => {
    const qall = (sql, params = []) => new Promise((resolve, reject) => db.all(sql, params, (e, r) => e ? reject(e) : resolve(r || [])));
    try {
      const days = Math.min(parseInt(req.query.days || '90', 10) || 90, 365);
      const bench = await qall("SELECT date, value, change_pct FROM benchmark_daily ORDER BY date DESC LIMIT ?", [days]);
      bench.reverse();
      const env = await qall('SELECT * FROM market_env ORDER BY date DESC LIMIT 1');
      const stat = await qall("SELECT day_return FROM fund_universe WHERE day_return IS NOT NULL");
      let up = 0, down = 0, flat = 0, sum = 0;
      for (const r of stat) {
        if (r.day_return > 0.0001) up++;
        else if (r.day_return < -0.0001) down++;
        else flat++;
        sum += r.day_return;
      }
      const n = stat.length || 1;
      const bench5 = bench.slice(-5);
      res.json({
        benchmark: bench,
        market_env: env[0] || null,
        stats: {
          fund_count: stat.length, up, down, flat,
          avg_return: Math.round(sum / n * 100) / 100,
          up_pct: Math.round(up / n * 1000) / 10,
          bench_5d: bench5.map(b => ({ date: b.date, change_pct: Math.round(b.change_pct * 100) / 100 }))
        }
      });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.get('/ai/daily', async (req, res) => {
    try {
      const userId = req.query.user_id || getCurrentUser();
      const rows = await new Promise((resolve, reject) => {
        db.all('SELECT date, total_assets, daily_pnl, cash, market_value FROM portfolio_daily WHERE user_id = ? ORDER BY date ASC', [userId], (e, rows) => e ? reject(e) : resolve(rows || []));
      });
      res.json(rows);
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.get('/daily-recap', (req, res) => {
    const userId = req.query.user_id || getCurrentUser();
    db.all('SELECT * FROM reports WHERE user_id = ? AND report_type = ? ORDER BY id DESC LIMIT 7', [userId, 'daily'], (e, rows) => {
      if (e) return res.status(500).json({ error: e.message });
      res.json({ recaps: rows || [] });
    });
  });

  r.get('/funds/:code/profile', (req, res) => {
    db.get('SELECT * FROM fund_profiles WHERE fund_code = ?', [req.params.code], (e, row) => {
      if (e) return res.status(500).json({ error: e.message });
      res.json({ profile: row || null });
    });
  });

  r.get('/funds/:code/research', (req, res) => {
    const userId = req.query.user_id || getCurrentUser();
    const limit = Math.min(parseInt(req.query.limit) || 20, 100);
    db.all('SELECT * FROM research_notes WHERE user_id = ? AND fund_code = ? ORDER BY id DESC LIMIT ?', [userId, req.params.code, limit], (e, rows) => {
      if (e) return res.status(500).json({ error: e.message });
      res.json({ notes: rows || [] });
    });
  });

  r.get('/alerts', (req, res) => {
    const userId = req.query.user_id || getCurrentUser();
    const limit = Math.min(parseInt(req.query.limit) || 50, 200);
    db.all('SELECT * FROM risk_events WHERE user_id = ? ORDER BY id DESC LIMIT ?', [userId, limit], (e, events) => {
      if (e) return res.status(500).json({ error: e.message });
      db.all('SELECT * FROM data_quality_logs ORDER BY id DESC LIMIT 20', [], (e2, dq) => {
        if (e2) return res.status(500).json({ error: e2.message });
        res.json({ events: events || [], data_quality: dq || [] });
      });
    });
  });

  r.get('/market-env', (req, res) => {
    db.all('SELECT * FROM market_env ORDER BY date DESC LIMIT 30', [], (e, rows) => {
      if (e) return res.status(500).json({ error: e.message });
      res.json({ market: rows || [] });
    });
  });

  r.get('/risk/events', (req, res) => {
    const userId = req.query.user_id || getCurrentUser();
    const limit = Math.min(parseInt(req.query.limit) || 50, 200);
    db.all('SELECT * FROM risk_events WHERE user_id = ? ORDER BY id DESC LIMIT ?', [userId, limit], (e, rows) => {
      if (e) return res.status(500).json({ error: e.message });
      res.json({ events: rows });
    });
  });

  r.get('/risk/params/:user_id', async (req, res) => {
    try {
      const cfg = await getRiskParams(req.params.user_id);
      res.json({ user_id: req.params.user_id, params: cfg });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.get('/orders', (req, res) => {
    const userId = req.query.user_id || getCurrentUser();
    const limit = Math.min(parseInt(req.query.limit) || 50, 200);
    db.all('SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT ?', [userId, limit], (e, rows) => {
      if (e) return res.status(500).json({ error: e.message });
      res.json({ orders: rows });
    });
  });

  r.get('/audit', (req, res) => {
    const limit = Math.min(parseInt(req.query.limit) || 100, 500);
    db.all('SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?', [limit], (e, rows) => {
      if (e) return res.status(500).json({ error: e.message });
      res.json({ logs: rows });
    });
  });

  r.get('/benchmark', async (req, res) => {
    try {
      const limit = Math.min(parseInt(req.query.limit) || 60, 500);
      const rows = await new Promise((resolve, reject) => {
        db.all('SELECT * FROM benchmark_daily ORDER BY date DESC LIMIT ?', [limit], (e, rows) => e ? reject(e) : resolve(rows || []));
      });
      res.json({ benchmark: rows.reverse() });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.get('/performance/:user_id', async (req, res) => {
    try {
      const rows = await new Promise((resolve, reject) => {
        db.all('SELECT * FROM performance_daily WHERE user_id = ? ORDER BY date', [req.params.user_id], (e, rows) => e ? reject(e) : resolve(rows || []));
      });
      res.json({ user_id: req.params.user_id, performance: rows });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  return r;
};
