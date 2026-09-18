# -*- coding: utf-8 -*-
"""server.js 新增 GET /api/ai/compare（双 AI 基金经理经营对比：账户/收益/费用/操作/每日资产曲线/持仓对比）"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """// 费用统计：汇总 + 按基金分组 + 逐笔明细（含费率，可追溯每笔组成）"""
new = """// 双 AI 基金经理经营对比（默认稳健 vs 激进）
app.get('/api/ai/compare', async (req, res) => {
  const qall = (sql, params = []) => new Promise((resolve, reject) => db.all(sql, params, (e, r) => e ? reject(e) : resolve(r || [])));
  const qget = (sql, params = []) => new Promise((resolve, reject) => db.get(sql, params, (e, r) => e ? reject(e) : resolve(r || null)));
  try {
    const users = Object.keys(userConfigs).filter(u => userConfigs[u]);
    const out = { users: [], daily: [], holdings: [] };
    const dailyMap = {};
    for (const userId of users) {
      const pf = await getUserPortfolio(userId);
      const mvTotal = await new Promise((resolve) => {
        db.all('SELECT fund_code, shares FROM holdings WHERE user_id = ? AND shares > 0', [userId], (err, rows) => {
          if (err) return resolve(0);
          let sum = 0; let pending = 0;
          const doEach = async () => {
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
        db.all('SELECT transaction_type, SUM(fees) AS fee FROM transactions WHERE user_id = ? GROUP BY transaction_type', [userId], (err, rows) => {
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
      // 每日资产序列
      const days = await qall('SELECT date, total_assets FROM portfolio_daily WHERE user_id = ? ORDER BY date ASC', [userId]);
      days.forEach(d => { (dailyMap[d.date] = dailyMap[d.date] || { date: d.date })[userId] = Math.round(d.total_assets * 100) / 100; });
    }
    out.daily = Object.values(dailyMap).sort((a, b) => a.date.localeCompare(b.date));
    // 持仓对比（两账户并排）
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
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// 费用统计：汇总 + 按基金分组 + 逐笔明细（含费率，可追溯每笔组成）"""
assert s.count(old) == 1, 'anchor not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('compare api added')
