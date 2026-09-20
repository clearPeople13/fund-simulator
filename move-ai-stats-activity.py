import io

# 1) readonly.js 加 /ai/stats 和 /ai/activity
p1 = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\routes\readonly.js"
with io.open(p1, 'r', encoding='utf-8') as f:
    s1 = f.read()
old = "  r.get('/ai/fees', async (req, res) => {"
new = """  r.get('/ai/stats', async (req, res) => {
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

  r.get('/ai/fees', async (req, res) => {"""
assert s1.count(old) == 1
s1 = s1.replace(old, new)
with io.open(p1, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s1)

# 2) server.js 删 /api/ai/stats + /api/ai/activity 块
p2 = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p2, 'r', encoding='utf-8') as f:
    s2 = f.read()
start = s2.find("app.get('/api/ai/stats', async (req, res) => {")
assert start != -1
end = s2.find("// 用户管理API", start)
assert end != -1
s2 = s2[:start] + "// /api/ai/stats + /api/ai/activity 已抽到 routes/readonly.js\n" + s2[end:]
with io.open(p2, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s2)
print('stats+activity moved')
