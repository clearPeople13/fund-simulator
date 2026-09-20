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

  r.get('/ai/stats', async (req, res) => {
    try {
      const userId = req.query.user_id || getCurrentUser();
      const q = (sql, params = []) => new Promise((resolve, reject) => db.get(sql, params, (e, r) => e ? reject(e) : resolve(r)));
      const all = (sql, params = []) => new Promise((resolve, reject) => db.all(sql, params, (e, r) => e ? reject(e) : resolve(r || [])));
      const buyRow = await q('SELECT COUNT(*) c, COALESCE(SUM(fees),0) f FROM transactions WHERE user_id = ? AND transaction_type = ?', [userId, 'BUY']);
      const sellRow = await q('SELECT COUNT(*) c FROM transactions WHERE user_id = ? AND transaction_type = ?', [userId, 'SELL']);
      const realizedRow = await q('SELECT COALESCE(SUM(amount),0) a, COUNT(*) c FROM realized_pnl WHERE user_id = ?', [userId]);
      const winRow = await q('SELECT COUNT(*) c FROM realized_pnl WHERE user_id = ? AND amount > 0', [userId]);
      const sells = await all('SELECT fund_code, transaction_date FROM transactions WHERE user_id = ? AND transaction_type = ?', [userId, 'SELL']);
      let holdDays = [];
      for (const sd of sells) {
        const b = await q('SELECT MIN(transaction_date) d FROM transactions WHERE user_id = ? AND fund_code = ? AND transaction_type = ?', [userId, sd.fund_code, 'BUY']);
        if (b && b.d) {
          const days = Math.max(0, Math.round((new Date(String(sd.transaction_date).slice(0,10)) - new Date(String(b.d).slice(0,10))) / 86400000));
          holdDays.push(days);
        }
      }
      const avgHold = holdDays.length ? holdDays.reduce((x, y) => x + y, 0) / holdDays.length : 0;
      const riskRow = await q('SELECT event_type, COUNT(*) c FROM risk_events WHERE user_id = ? GROUP BY event_type', [userId]);
      const risks = {};
      if (riskRow) risks[riskRow.event_type] = riskRow.c;
      const addRow = await q("SELECT COUNT(*) c FROM orders WHERE user_id = ? AND order_type = 'BUY' AND reason LIKE '%加仓%'", [userId]);
      const rebRow = await q("SELECT COUNT(*) c FROM orders WHERE user_id = ? AND reason LIKE '%再平衡%'", [userId]);
      const watchRow = await q('SELECT COUNT(*) c FROM watchlist WHERE user_id = ?', [userId]);
      const anaRow = await q('SELECT COUNT(DISTINCT analysis_time) c FROM analysis_logs WHERE user_id = ?', [userId]);
      res.json({
        user_id: userId,
        buy_count: buyRow.c || 0, sell_count: sellRow.c || 0,
        total_trades: (buyRow.c || 0) + (sellRow.c || 0),
        buy_fee: Math.round((buyRow.f || 0) * 100) / 100,
        realized_pnl: Math.round((realizedRow.a || 0) * 100) / 100,
        realized_count: realizedRow.c || 0,
        win_count: winRow.c || 0,
        win_rate: (realizedRow.c || 0) > 0 ? Math.round((winRow.c / realizedRow.c) * 1000) / 10 : 0,
        avg_hold_days: Math.round(avgHold * 10) / 10,
        stop_loss_count: risks.STOP_LOSS || 0,
        stop_profit_count: risks.STOP_PROFIT || 0,
        reduce_count: risks.REDUCE || 0,
        add_count: addRow.c || 0,
        rebalance_count: rebRow.c || 0,
        watchlist_count: watchRow.c || 0,
        analysis_rounds: anaRow.c || 0
      });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.get('/ai/activity', async (req, res) => {
    try {
      const userId = req.query.user_id || getCurrentUser();
      const limit = Math.min(parseInt(req.query.limit) || 15, 50);
      const all = (sql, params = []) => new Promise((resolve, reject) => db.all(sql, params, (e, r) => e ? reject(e) : resolve(r || [])));
      const nameOf = async (code) => {
        if (!code) return '';
        const f = await new Promise((resolve) => db.get('SELECT fund_name FROM funds WHERE fund_code = ?', [code], (e, r) => resolve(r || null)));
        return f ? f.fund_name : code;
      };
      const items = [];
      const txs = await all('SELECT transaction_type, fund_code, amount, shares, fees, transaction_date, reason FROM transactions WHERE user_id = ? ORDER BY transaction_date DESC LIMIT 8', [userId]);
      for (const t of txs) {
        items.push({ time: t.transaction_date, type: t.transaction_type === 'BUY' ? 'buy' : 'sell', title: `${t.transaction_type === 'BUY' ? '买入' : '卖出'} ${t.fund_code} ${t.fund_code}`, desc: `${t.transaction_type === 'BUY' ? '买入' : '卖出'} ¥${(t.amount || 0).toFixed(2)}（${(t.shares || 0).toLocaleString()} 份）· 手续费 ¥${(t.fees || 0).toFixed(2)}${t.reason ? ' · ' + t.reason : ''}` });
      }
      const ords = await all("SELECT order_type, fund_code, amount, shares, price, status, reason, created_at FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 6", [userId]);
      for (const o of ords) {
        items.push({ time: o.created_at, type: o.status === 'SUBMITTED' ? 'pending' : 'order', title: `${o.order_type === 'BUY' ? '买入' : '卖出'}订单 ${o.fund_code}${o.status === 'SUBMITTED' ? '（待确认）' : ''}`, desc: o.reason || `金额 ¥${(o.amount || 0).toFixed(2)}` });
      }
      const risks = await all('SELECT event_type, fund_code, detail, created_at FROM risk_events WHERE user_id = ? ORDER BY created_at DESC LIMIT 6', [userId]);
      for (const rv of risks) {
        items.push({ time: rv.created_at, type: 'risk', title: `风控：${rv.event_type} ${rv.fund_code}`, desc: rv.detail || '' });
      }
      const audits = await all("SELECT actor, action, target, detail, created_at FROM audit_logs WHERE target LIKE ? ORDER BY created_at DESC LIMIT 6", ['%' + userId + '%']);
      for (const au of audits) {
        items.push({ time: au.created_at, type: 'audit', title: `${au.actor} · ${au.action}${au.target ? ' ' + au.target : ''}`, desc: (au.detail || '').slice(0, 120) });
      }
      const anas = await all("SELECT analysis_type, fund_code, decision, confidence, entry_price, target_price, stop_loss, analysis_time, signal_label, signal_reason FROM analysis_logs WHERE user_id = ? ORDER BY analysis_time DESC LIMIT 5", [userId]);
      for (const a of anas) {
        if (a.analysis_type === 'hotspot') {
          items.push({ time: a.analysis_time, type: 'hotspot', title: `热点分析 ${a.signal_label || '市场'} → ${a.decision}`, desc: a.signal_reason || '' });
        } else {
          items.push({ time: a.analysis_time, type: 'analysis', title: `分析 ${a.fund_code} → ${a.decision}${a.confidence ? '（' + a.confidence + '）' : ''}`, desc: `参考价 ¥${(a.entry_price || 0).toFixed(4)} · 目标 ¥${(a.target_price || 0).toFixed(4)} · 止损 ¥${(a.stop_loss || 0).toFixed(4)}` });
        }
      }
      items.sort((x, y) => String(y.time).localeCompare(String(x.time)));
      const out = [];
      for (const it of items.slice(0, limit)) {
        const codeMatch = it.title.match(/(\d{6})/);
        const nm = codeMatch ? await nameOf(codeMatch[1]) : '';
        out.push({ ...it, fund_name: nm });
      }
      res.json({ list: out });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.get('/ai/fees', async (req, res) => {
    try {
      const userId = req.query.user_id || getCurrentUser();
      const rows = await new Promise((resolve, reject) => {
        db.all(`SELECT t.id, t.transaction_date, t.fund_code, t.transaction_type, t.amount, t.price, t.shares, t.fees,
                COALESCE(f.fund_name, t.fund_code) AS fund_name
                FROM transactions t LEFT JOIN funds f ON f.fund_code = t.fund_code
                WHERE t.user_id = ? ORDER BY t.transaction_date ASC, t.id ASC`, [userId], (e, r) => e ? reject(e) : resolve(r || []));
      });
      const round2 = v => Math.round(v * 100) / 100;
      const detail = rows.map(t => ({
        id: t.id, transaction_date: t.transaction_date, fund_code: t.fund_code,
        fund_name: t.fund_name, transaction_type: t.transaction_type, amount: t.amount,
        shares: t.shares, price: t.price, fees: round2(t.fees || 0),
        rate: t.amount > 0 ? Number((((t.fees || 0) / t.amount) * 100).toFixed(4)) : 0
      }));
      let buy_fee = 0, sell_fee = 0;
      const byFund = {};
      rows.forEach(t => {
        const f = t.fees || 0;
        if (t.transaction_type === 'BUY') buy_fee += f; else if (t.transaction_type === 'SELL') sell_fee += f;
        if (!byFund[t.fund_code]) byFund[t.fund_code] = { fund_code: t.fund_code, fund_name: t.fund_name, buy_fee: 0, sell_fee: 0, buy_count: 0, sell_count: 0, buy_amount: 0, sell_amount: 0 };
        const g = byFund[t.fund_code];
        if (t.transaction_type === 'BUY') { g.buy_fee += f; g.buy_count++; g.buy_amount += t.amount; }
        else if (t.transaction_type === 'SELL') { g.sell_fee += f; g.sell_count++; g.sell_amount += t.amount; }
      });
      const by_fund = Object.values(byFund).map(g => ({
        ...g, buy_fee: round2(g.buy_fee), sell_fee: round2(g.sell_fee),
        total_fee: round2(g.buy_fee + g.sell_fee),
        buy_rate: g.buy_amount > 0 ? Number(((g.buy_fee / g.buy_amount) * 100).toFixed(4)) : 0,
        sell_rate: g.sell_amount > 0 ? Number(((g.sell_fee / g.sell_amount) * 100).toFixed(4)) : 0
      }));
      res.json({
        user_id: userId,
        summary: { buy_fee: round2(buy_fee), sell_fee: round2(sell_fee), total_fee: round2(buy_fee + sell_fee), trade_count: rows.length },
        by_fund, detail
      });
    } catch (e) { res.status(500).json({ error: e.message }); }
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
