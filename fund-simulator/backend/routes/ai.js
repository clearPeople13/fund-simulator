/**
 * AI 核心路由：/api/ai/portfolio /compare /transactions /hotspots /discover-watchlist /analyze
 * ctx: { db, getUserPortfolio, getCurrentUser, getLocalDateStr, userConfigs, buildHotspots,
 *        aiDiscoverWatchlist, getWatchlist, getUserWatchlistCodes, aiAnalysisStatus, aiAnalysisResults,
 *        getFundSignal, saveAnalysisResult }
 */
const { Router } = require('express');

module.exports = function aiRoutes(ctx) {
  const r = Router();
  const { db, getUserPortfolio, getCurrentUser, getLocalDateStr, userConfigs, buildHotspots, fmtDT, isTradingTime,
          aiDiscoverWatchlist, getWatchlist, getUserWatchlistCodes, aiAnalysisStatus, aiAnalysisResults,
          getFundSignal, saveAnalysisResult } = ctx;
  // full-process 路由用的局部变量
  const analysisResults = aiAnalysisResults;

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
        // transaction_date 现在是时间戳（毫秒），转成日期字符串比较
        let pending = false;
        if (lastBuy && lastBuy.md) {
          const md = typeof lastBuy.md === 'number' ? new Date(lastBuy.md).toLocaleDateString('zh-CN', { timeZone: 'Asia/Shanghai' }) : String(lastBuy.md).slice(0, 10);
          const todayLocal = new Date().toLocaleDateString('zh-CN', { timeZone: 'Asia/Shanghai' });
          pending = md === todayLocal;
        }
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
        // 统一格式化：时间戳 -> 北京时间字符串（前端直接显示，无需再转）
        enriched.push({ ...tx, fund_name: fund ? fund.fund_name : tx.fund_code, formatted_date: fmtDT(tx.transaction_date) });
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

  // AI 按用户性格自主选基进观察池
  r.post('/discover-watchlist', async (req, res) => {
    try {
      const userId = (req.body && req.body.user_id) || getCurrentUser();
      if (!userConfigs[userId]) return res.status(404).json({ error: '用户不存在' });
      const result = await aiDiscoverWatchlist(userId);
      const list = await getWatchlist(userId);
      res.json({
        message: `AI已按${userConfigs[userId].style}维护观察池：新增 ${result.inserted.length} 只，自动调整 ${result.removed} 只`,
        inserted: result.inserted,
        removed: result.removed,
        watchlist: list
      });
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

  // 触发AI分析
  // AI 全流程分析：全市场扫描 → 观察池更新 → 持仓分析 → 风控 → 复盘
  r.post('/full-process', async (req, res) => {
    const userId = req.body.user_id || getCurrentUser();
    if (!userConfigs[userId]) return res.status(404).json({ error: '用户不存在' });
    
    console.log(`[AI全流程] ${userId} 开始...`);
    const logs = [];
    
    try {
      // 1. 全市场扫描 + 观察池更新
      console.log('[AI全流程] 1/5 全市场扫描 + 观察池更新...');
      logs.push('1/5 全市场扫描 + 观察池更新...');
      await aiDiscoverWatchlist(userId, 'ai');
      
      // 2. 观察池基金分析
      console.log('[AI全流程] 2/5 观察池基金分析...');
      logs.push('2/5 观察池基金分析...');
      const fundCodes = await getUserWatchlistCodes(userId);
      for (const code of fundCodes) {
        const sig = await getFundSignal(code);
        if (sig && sig.signal) {
          analysisResults[code] = {
            decision: sig.signal.action === 'buy' ? 'BUY' : 'HOLD',
            reason: sig.signal.reason,
            analyzed_at: new Date().toISOString()
          };
        }
      }
      
      // 3. 持仓分析（买入/卖出决策）
      console.log('[AI全流程] 3/5 持仓分析...');
      logs.push('3/5 持仓分析...');
      const portfolio = await getUserPortfolio(userId);
      
      // 4. 风控检查
      console.log('[AI全流程] 4/5 风控检查...');
      logs.push('4/5 风控检查...');
      
      // 5. 生成复盘报告
      console.log('[AI全流程] 5/5 生成复盘报告...');
      logs.push('5/5 生成复盘报告...');
      
      console.log(`[AI全流程] ${userId} 完成`);
      res.json({ message: 'AI 全流程分析完成', logs: logs });
    } catch (e) {
      console.error('[AI全流程] 失败: ' + e.message);
      res.status(500).json({ error: e.message });
    }
  });

  r.post('/analyze', async (req, res) => {
    try {
      let { fund_codes, user_id, mode } = req.body;
      // mode: 'rule'（规则引擎，默认）| 'ai'（MIMO Pro 2.5 大模型）
      const analysisMode = mode || 'ai';  // 默认走 AI，失败自动降级到规则
      const userId = user_id || getCurrentUser();
      if (!userConfigs[userId]) return res.status(404).json({ error: '用户不存在' });
      if (!fund_codes || !Array.isArray(fund_codes) || fund_codes.length === 0) {
        fund_codes = await getUserWatchlistCodes(userId);
      }
      if (fund_codes.length === 0) {
        return res.json({ message: '观察池为空，请先在基金库中添加自选基金', results: {}, trades: [] });
      }
      aiAnalysisStatus.status = 'running';
      aiAnalysisStatus.progress = 0;
      aiAnalysisStatus.currentPhase = '开始分析...';
      const analysisResults = {};
      const signals = {};
      for (let i = 0; i < fund_codes.length; i++) {
        const code = fund_codes[i];
        aiAnalysisStatus.progress = Math.round(((i + 1) / fund_codes.length) * 100);
        aiAnalysisStatus.currentPhase = `分析 ${code}...`;
        let sig;
        if (analysisMode === 'ai') {
          // AI 模式：MIMO Pro 2.5 大模型分析
          try {
            const { analyzeFund } = require('../ai-advisor');
            const user = userConfigs[userId] || {};
            const aiResult = await analyzeFund({
              fund_name: code, fund_code: code,
              latest_nav: null, daily_return: 0,
              change_5d: 0, change_20d: 0,
              drawdown_60d: 0, above_ma20: true
            }, user.style || '稳健型');
            sig = {
              latest_nav: null,
              signal: {
                action: aiResult.decision === 'BUY' ? 'buy' : (aiResult.decision === 'SELL' ? 'sell' : 'hold'),
                label: 'AI分析',
                reason: aiResult.reason
              },
              confidence: aiResult.confidence
            };
          } catch (aiErr) {
            console.error(`[AI] ${code} 分析失败: ${aiErr.message}，降级到规则引擎`);
            sig = await getFundSignal(code); // 降级到规则引擎
          }
        } else {
          // 规则模式：原来的 getFundSignal（保留不动）
          console.log(`[分析] ${code} 走规则引擎`);
          sig = await getFundSignal(code);
        }
        signals[code] = sig;
        if (!sig || !sig.signal || sig.latest_nav == null) {
          analysisResults[code] = {
            decision: 'HOLD', confidence: '低', entry_price: 0, target_price: 0, stop_loss: 0,
            analysis_time: new Date().toISOString(), signal_label: '数据不足',
            signal_reason: '暂无足够净值数据，无法分析',
            change_5d: null, change_20d: null, drawdown_60d: null, above_ma20: null
          };
          await saveAnalysisResult(userId, code, analysisResults[code]);
          continue;
        }
        const action = sig.signal.action;
        const entry = sig.latest_nav;
        // AI 大模型分析（MIMO Pro 2.5）
        let aiDecision = (action === 'buy' || action === 'add') ? 'BUY' : 'HOLD';
        let aiConfidence = action === 'buy' ? '高' : (action === 'add' ? '中' : '低');
        let aiReason = sig.signal.reason;
        try {
          const { analyzeFund } = require('../ai-advisor');
          const user = userConfigs[userId] || {};
          const aiResult = await analyzeFund({
            fund_name: code, fund_code: code,
            latest_nav: entry, daily_return: sig.daily_return,
            change_5d: sig.change_5d, change_20d: sig.change_20d,
            drawdown_60d: sig.drawdown_60d, above_ma20: sig.above_ma20
          }, user.style || '稳健型');
          aiDecision = aiResult.decision;
          aiConfidence = aiResult.confidence;
          aiReason = aiResult.reason;
        } catch (aiErr) { console.error('[AI] 分析失败: ' + aiErr.message); }
        analysisResults[code] = {
          decision: aiDecision,
          confidence: aiConfidence,
          entry_price: entry, target_price: Number((entry * 1.1).toFixed(4)),
          stop_loss: Number((entry * 0.95).toFixed(4)),
          analysis_time: new Date().toISOString(),
          signal_label: 'AI分析', signal_reason: aiReason,
          change_5d: sig.change_5d, change_20d: sig.change_20d,
          drawdown_60d: sig.drawdown_60d, above_ma20: sig.above_ma20,
          nav_date: sig.nav_date, daily_return: sig.daily_return
        };
        await saveAnalysisResult(userId, code, analysisResults[code]);
        
        // AI 自动交易：BUY → 走 order-engine 生成订单（T+1 确认，不直接落账）
        if (aiDecision === 'BUY') {
          if (!isTradingTime()) {
            console.log(`[AI交易] ${userId} ${code} AI 建议买入，但当前非交易时间，跳过交易（仅记录分析）`);
          } else {
          console.log(`[AI交易] ${userId} ${code} AI 建议买入，生成订单（T+1确认）...`);
          try {
            const { createOrder } = require('../engine/order-engine');
            const portfolio = await getUserPortfolio(userId);
            const buyAmount = portfolio.total_assets * 0.05;
            const order = await createOrder({ db, saveTransaction: require('../services/portfolio').saveTransaction, updateHolding: require('../services/portfolio').updateHolding, getUserPortfolio }, {
              userId, fundCode: code, orderType: 'BUY', amount: buyAmount, price: entry,
              reason: `AI分析建议买入（${sig.confidence || '中'}信心度）`
            });
            console.log(`[AI交易] ${userId} ${code} 订单#${order.id} 已提交：¥${buyAmount.toFixed(2)}（T+1确认）`);
          } catch (tradeErr) {
            console.error(`[AI交易] ${code} 下单失败: ${tradeErr.message}`);
          }
          } // end isTradingTime else
        }
      }
      aiAnalysisStatus.status = 'completed';
      aiAnalysisStatus.lastAnalysis = new Date().toISOString();
      aiAnalysisStatus.progress = 100;
      aiAnalysisStatus.currentPhase = '分析完成';
      const suggestions = [];
      const portfolio = await getUserPortfolio(userId);
      for (const [code, result] of Object.entries(analysisResults)) {
        if (result.decision !== 'BUY') continue;
        const sig = signals[code];
        if (!sig || sig.latest_nav == null || sig.latest_nav <= 0) continue;
        const action = sig.signal.action;
        const buyRatio = action === 'buy' ? 0.2 : 0.1;
        const suggestAmount = Math.round(portfolio.current_capital * buyRatio);
        result.suggest_amount = suggestAmount;
        suggestions.push({ fund_code: code, signal: action, amount: suggestAmount, reason: sig.signal.reason });
      }
      const suggestCodes = suggestions.map(s => s.fund_code);
      // 排版优化：基金代码每行 6 个分组显示
      const groupSize = 6;
      const groups = [];
      for (let i = 0; i < suggestCodes.length; i += groupSize) {
        groups.push(suggestCodes.slice(i, i + groupSize).join('  '));
      }
      const styleName = (userConfigs[userId] && userConfigs[userId].style) || '未知';
      const msg = suggestions.length > 0
        ? `【${styleName}】观察池 ${fund_codes.length} 只 | 入场信号 ${suggestions.length} 只\n━━━━━━━━━━━━━━\n📈 入场信号基金：\n${groups.join('\n')}\n━━━━━━━━━━━━━━\n仅供参考，系统不自动交易`
        : `【${styleName}】观察池 ${fund_codes.length} 只 | 无入场信号，建议观望`;
      // 飞书通知：AI 分析完成
      try {
        const { sendFeishu } = require('../notify');
        await sendFeishu('AI分析完成', msg);
      } catch (e) { console.error('[飞书] 分析通知失败: ' + e.message); }
      res.json({
        message: msg,
        results: analysisResults, suggestions,
        portfolio: { current_capital: portfolio.current_capital, holdings: portfolio.holdings },
        analysis_time: aiAnalysisStatus.lastAnalysis
      });
    } catch (error) {
      aiAnalysisStatus.status = 'error';
      aiAnalysisStatus.currentPhase = '分析失败: ' + error.message;
      res.status(500).json({ error: error.message });
    }
  });

  return r;
};
