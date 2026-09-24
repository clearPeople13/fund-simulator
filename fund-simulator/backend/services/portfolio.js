/**
 * 组合服务：getUserPortfolio / saveTransaction / updateHolding / getAnalysisResults
 * ctx: { db, userConfigs }
 */

function getUserPortfolio(ctx, userId) {
  const { db, userConfigs } = ctx;
  return new Promise((resolve, reject) => {
    const portfolio = {
      initial_capital: userConfigs[userId]?.initial_capital || 100000,
      current_capital: userConfigs[userId]?.initial_capital || 100000,
      holdings: {},
      transactions: []
    };
    db.all('SELECT SUM(amount) AS total FROM realized_pnl WHERE user_id = ?', [userId], (errPnl, pnlRows) => {
      if (errPnl) { reject(errPnl); return; }
      const realizedTotal = (pnlRows && pnlRows[0] && pnlRows[0].total) || 0;
      portfolio.realized_pnl = realizedTotal;
      db.all('SELECT * FROM holdings WHERE user_id = ?', [userId], (err, holdings) => {
        if (err) { reject(err); return; }
        holdings.forEach(h => {
          portfolio.holdings[h.fund_code] = { shares: h.shares, cost: h.cost_price, total_cost: h.total_cost };
          portfolio.current_capital -= h.total_cost;
        });
        portfolio.current_capital += realizedTotal;
        db.all('SELECT * FROM transactions WHERE user_id = ? ORDER BY transaction_date DESC', [userId], (err, transactions) => {
          if (err) { reject(err); return; }
          portfolio.transactions = transactions;
          resolve(portfolio);
        });
      });
    });
  });
}

function saveTransaction(ctx, userId, transaction) {
  const { db } = ctx;
  return new Promise((resolve, reject) => {
    // 支持传 transaction_date（成交日）；不传则用数据库默认 CURRENT_TIMESTAMP
    const hasDate = !!transaction.transaction_date;
    const cols = hasDate
      ? `(user_id, fund_code, transaction_type, amount, price, shares, fees, reason, remaining_shares, transaction_date)`
      : `(user_id, fund_code, transaction_type, amount, price, shares, fees, reason, remaining_shares)`;
    const placeholders = hasDate
      ? `(?, ?, ?, ?, ?, ?, ?, ?, CASE WHEN ? = 'BUY' THEN ? ELSE NULL END, ?)`
      : `(?, ?, ?, ?, ?, ?, ?, ?, CASE WHEN ? = 'BUY' THEN ? ELSE NULL END)`;
    const sql = `INSERT INTO transactions ${cols} VALUES ${placeholders}`;
    const params = hasDate
      ? [userId, transaction.fund_code, transaction.action, transaction.amount, transaction.price,
         transaction.shares, transaction.fees || 0, transaction.reason, transaction.action, transaction.shares, transaction.transaction_date]
      : [userId, transaction.fund_code, transaction.action, transaction.amount, transaction.price,
         transaction.shares, transaction.fees || 0, transaction.reason, transaction.action, transaction.shares];
    db.run(sql, params, function(err) {
      if (err) { reject(err); } else { resolve(this.lastID); }
    });
  });
}

function updateHolding(ctx, userId, fundCode, shares, costPrice, totalCost) {
  const { db } = ctx;
  return new Promise((resolve, reject) => {
    const sql = `INSERT OR REPLACE INTO holdings (user_id, fund_code, shares, cost_price, total_cost, updated_at)
                 VALUES (?, ?, ?, ?, ?, ?)`;
    db.run(sql, [userId, fundCode, shares, costPrice, totalCost, Date.now()], function(err) {
      if (err) { reject(err); } else { resolve(); }
    });
  });
}

function getAnalysisResults(ctx, userId) {
  const { db } = ctx;
  return new Promise((resolve, reject) => {
    db.all('SELECT * FROM ai_analysis WHERE user_id = ? ORDER BY analysis_time DESC', [userId], (err, rows) => {
      if (err) { reject(err); return; }
      const results = {};
      rows.forEach(row => {
        results[row.fund_code] = {
          decision: row.decision, confidence: row.confidence,
          entry_price: row.entry_price, target_price: row.target_price,
          stop_loss: row.stop_loss, analysis_time: row.analysis_time
        };
      });
      resolve(results);
    });
  });
}

module.exports = { getUserPortfolio, saveTransaction, updateHolding, getAnalysisResults };
