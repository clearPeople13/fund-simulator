const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
const userId = 'aggressive';
const all = (sql, params = []) => new Promise((resolve, reject) => db.all(sql, params, (e, r) => e ? reject(e) : resolve(r || [])));
(async () => {
  try {
    const txs = await all('SELECT transaction_type, fund_code, amount, shares, fees, transaction_date, reason FROM transactions WHERE user_id = ? ORDER BY transaction_date DESC LIMIT 8', [userId]);
    console.log('txs ok', txs.length);
    const ords = await all("SELECT order_type, fund_code, amount, shares, price, status, reason, created_at FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 6", [userId]);
    console.log('ords ok', ords.length);
    const risks = await all('SELECT event_type, fund_code, detail, created_at FROM risk_events WHERE user_id = ? ORDER BY created_at DESC LIMIT 6', [userId]);
    console.log('risks ok', risks.length);
    const audits = await all("SELECT actor, action, target, detail, created_at FROM audit_logs WHERE user_id = ? OR target LIKE ? ORDER BY created_at DESC LIMIT 6", [userId, '%' + userId + '%']);
    console.log('audits ok', audits.length);
    const anas = await all('SELECT fund_code, decision, confidence, entry_price, target_price, stop_loss, analysis_time FROM analysis_logs WHERE user_id = ? ORDER BY analysis_time DESC LIMIT 4', [userId]);
    console.log('anas ok', anas.length, JSON.stringify(anas[0] || null));
  } catch (e) {
    console.error('FAIL:', e.message);
  } finally { db.close(); }
})();
