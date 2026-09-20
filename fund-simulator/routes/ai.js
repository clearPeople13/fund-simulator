/**
 * AI 核心查询路由：/api/ai/portfolio /api/ai/compare /api/ai/transactions /api/ai/hotspots
 * ctx: { db, getUserPortfolio, getCurrentUser, getLocalDateStr, userConfigs, buildHotspots }
 */
const { Router } = require('express');

module.exports = function aiRoutes(ctx) {
  const r = Router();
  const { db, getUserPortfolio, getCurrentUser, getLocalDateStr, userConfigs, buildHotspots } = ctx;

  // 获取AI持仓
  r.get('/portfolio', async (req, res) => {
    try {
      const userId = req.query.user_id || getCurrentUser();
      const portfolio = await getUserPortfolio(userId);
      const todayStr = new Date().toISOString().slice(0, 10);
      const holdings = {};
      for (const [code, h] of Object.entries(portfolio.holdings || {})) {
        const fund = await new Promise((resolve) => {
          db.get('SELECT fund_name, fund_type FROM funds WHERE fund_code = ?', [code], (e, row) => resolve(e ? null : row));
        });
        const lastBuy = await new Promise((resolve) => {
          db.get("SELECT MAX(transaction_date) AS md FROM transactions WHERE user_id = ? AND fund_code = ? AND transaction_type = 'BUY'", [userId, code], (e, row) => resolve(e ? null : row));
        });
        const pending = !!(lastBuy && lastBuy.md && lastBuy.md.slice(0, 10) === todayStr);
        const navRow = await new Promise((resolve) => {
          db.get('SELECT unit_nav, nav_date, daily_return FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1', [code], (e, row) => resolve(e ? null : row));
        });
        const latestNav = navRow ? navRow.unit_nav : null;
        const marketValue = pending ? h.total_cost : (latestNav ? h.shares * latestNav : h.total_cost);
        const realizedRow = await new Promise((resolve) => {
          db.get('SELECT SUM(amount) AS t FROM realized_pnl WHERE user_id = ? AND fund_code = ?', [userId, code], (e, row) => resolve(e ? null : row));
        });
        holdings[code] = {
          ...h, fund_name: fund ? fund.fund_name : code, fund_type: fund ? fund.fund_type : '', pending_confirm: pending,
          latest_nav: latestNav, nav_date: navRow ? navRow.nav_date : null, daily_return: navRow ? navRow.daily_return : null,
          market_value: marketValue,
          realized_pnl: realizedRow && realizedRow.t ? Math.round(realizedRow.t * 100) / 100 : 0
        };
      }
      const todayPnlRow = await new Promise((resolve) => {
        db.get('SELECT daily_pnl FROM portfolio_daily WHERE user_id = ? AND date = ?', [userId, getLocalDateStr()], (e, row) => resolve(e ? null : row));
      });
      const feeStats = await new Promise((resolve) => {
        db.all('SELECT transaction_type, SUM(fees) AS fee FROM transactions WHERE user_id = ? GROUP BY transaction_type', [userId], (e, rows) => {
          if (e) return resolve({ buy_fee: 0, sell_fee: 0, total_fee: 0 });
          let buy = 0, sell = 0;
          (rows || []).forEach(r => { if (r.transaction_type === 'BUY') buy += r.fee || 0; else if (r.transaction_type === 'SELL') sell += r.fee || 0; });
          const round2 = v => Math.round(v * 100) / 100;
          resolve({ buy_fee: round2(buy), sell_fee: round2(sell), total_fee: round2(buy + sell) });
        });
      });
      const marketValueTotal = Object.values(holdings).reduce((sum, h) => sum + (h.market_value || h.total_cost), 0);
      const realizedTotal = Object.values(holdings).reduce((sum, h) => sum + (h.realized_pnl || 0), 0);
      res.json({
        initial_capital: portfolio.initial_capital,
        current_capital: portfolio.current_capital,
        holdings,
        total_assets: portfolio.current_capital + marketValueTotal,
        realized_pnl: Math.round(realizedTotal * 100) / 100,
        today_pnl: todayPnlRow ? todayPnlRow.daily_pnl : null,
        fee_stats: feeStats
      });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  // 双 AI 基金经理经营对比
  r.get('/compare', async (req, res) => {
    const qall = (sql, params = []) => new Promise((resolve, reject) => db.all(sql, params, (e, r) => e ? reject(e) : resolve(r || [])));
    const qget = (sql, params = []) => new Promise((resolve, reject) => db.get(sql, params, (e, r) => e ? reject(e) : resolve(r || null)));
    try {
      const users = Object.keys(userConfigs).filter(u => userConfigs[u]);
      const out = { users: [], daily: [], holdings: [] };
      const dailyMap = {};
      for (const userId of users) {
        const pf = await getUserPortfolio(userId);
        const mvTotal = await new Promise((resolve) => {
          db.all('SELECT fund_code, shares FROM holdings WHERE user_id = ? AND shares > 0', [userId], (e, rows) => {
            if (e) return resolve(0);
            const doEach = async () => {
              let sum = 0;
              for (const r of rows || []) {
                const nav = await new Promise((res2) => db.get('SELECT unit_nav FROM fund_nav WHERE fund_code = ? ORDER BY nav_date DESC LIMIT 1', [r.fund_code], (e2, n) => res2(n || null)));
                sum += (nav && nav.unit_nav ? r.shares * nav.unit_nav : 0);
              }
              resolve(sum);
            };
            doEach();
          });
        });
        const feeStats = await new Promise((resolve) => {
          db.all('SELECT transaction_type, SUM(fees) AS fee FROM transactions WHERE user_id = ? GROUP BY transaction_type', [userId], (e, rows) => {
            let b = 0, s2 = 0; (rows || []).forEach(r => { if (r.transaction_type === 'BUY') b += r.fee || 0; else if (r.transaction_type === 'SELL') s2 += r.fee || 0; });
            resolve({ buy_fee: Math.round(b * 100) / 100, sell_fee: Math.round(s2 * 100) / 100, total_fee: Math.round((b + s2) * 100) / 100 });
          });
        });
        const realizedRow = await qget('SELECT SUM(amount) AS t FROM realized_pnl WHERE user_id = ?', [userId]);
        const realized = realizedRow && realizedRow.t ? Math.round(realizedRow.t * 100) / 100 : 0;
        const txCount = await qget('SELECT COUNT(*) c FROM transactions WHERE user_id = ?', [userId]);
        const wlCount = await qget('SELECT COUNT(*) c FROM watchlist WHERE user_id = ?', [userId]);
        const totalAssets = pf.current_capital + mvTotal;
        const initial = pf.initial_capital || 100000;
        const cfg = userConfigs[userId] || {};
        out.users.push({
          id: userId, name: cfg.name || userId, style: cfg.style || '', avatar: cfg.avatar || '👤',
          initial_capital: initial, total_assets: Math.round(totalAssets * 100) / 100,
          total_return: Math.round((totalAssets - initial) * 100) / 100,
          total_return_pct: Math.round((totalAssets / initial - 1) * 10000) / 100,
          cash: Math.round(pf.current_capital * 100) / 100,
          market_value: Math.round(mvTotal * 100) / 100,
          realized_pnl: realized, fee_stats: feeStats,
          tx_count: txCount ? txCount.c : 0, watchlist_count: wlCount ? wlCount.c : 0,
          holding_count: Object.keys(pf.holdings || {}).filter(c => pf.holdings[c].shares > 0).length
        });
        const days = await qall('SELECT date, total_assets FROM portfolio_daily WHERE user_id = ? ORDER BY date ASC', [userId]);
        days.forEach(d => { (dailyMap[d.date] = dailyMap[d.date] || { date: d.date })[userId] = Math.round(d.total_assets * 100) / 100; });
      }
      out.daily = Object.values(dailyMap).sort((a, b) => a.date.localeCompare(b.date));
      const codes = new Set();
      for (const userId of users) {
        const hs = await qall('SELECT fund_code, shares, total_cost FROM holdings WHERE user_id = ? AND shares > 0', [userId]);
        hs.forEach(h => codes.add(h.fund_code));
      }
      for (const code of codes) {
        const fund = await qget('SELECT fund_name, fund_type FROM funds WHERE fund_code = ?', [code]);
        const row = { fund_code: code, fund_name: fund ? fund.fund_name : code, fund_type: fund ? fund.fund_type : '' };
        for (const userId of users) {
          const h = await qget('SELECT shares, total_cost FROM holdings WHERE user_id = ? AND fund_code = ?', [userId, code]);
          row[userId] = h && h.shares > 0 ? { shares: Math.round(h.shares * 100) / 100, total_cost: Math.round(h.total_cost * 100) / 100 } : null;
        }
        out.holdings.push(row);
      }
      res.json(out);
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  // 获取AI交易记录
  r.get('/transactions', async (req, res) => {
    try {
      const userId = req.query.user_id || getCurrentUser();
      const portfolio = await getUserPortfolio(userId);
      const txs = portfolio.transactions || [];
      const enriched = [];
      for (const tx of txs) {
        const fund = await new Promise((resolve) => {
          db.get('SELECT fund_name FROM funds WHERE fund_code = ?', [tx.fund_code], (e, row) => resolve(e ? null : row));
        });
        enriched.push({ ...tx, fund_name: fund ? fund.fund_name : tx.fund_code });
      }
      const pendingRows = await new Promise((resolve, reject) => {
        db.all("SELECT id, fund_code, order_type, amount, shares, price, fee, status, order_date, trade_date, reason FROM orders WHERE user_id = ? AND status = 'SUBMITTED' ORDER BY id DESC", [userId], (e, rows) => e ? reject(e) : resolve(rows || []));
      });
      const pending = [];
      for (const p of pendingRows) {
        const fund = await new Promise((resolve) => {
          db.get('SELECT fund_name FROM funds WHERE fund_code = ?', [p.fund_code], (e, row) => resolve(e ? null : row));
        });
        pending.push({ ...p, fund_name: fund ? fund.fund_name : p.fund_code });
      }
      res.json({ list: enriched, pending });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  // 市场热点分析
  r.get('/hotspots', async (req, res) => {
    try {
      const userId = req.query.user_id || getCurrentUser();
      if (!userConfigs[userId]) return res.status(404).json({ error: '用户不存在' });
      const data = await buildHotspots(userId);
      res.json(data);
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  return r;
};
