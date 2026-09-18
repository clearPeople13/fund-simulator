/**
 * 订单执行引擎（真实时间申赎）
 * 规格来源：fund/AI_FUND_OPERATIONS_DESIGN.md §3.3 §4.4 §5.2
 *
 * 状态机：
 *   CREATED(草稿) → SUBMITTED(T日下单，按T日净值) → CONFIRMED(T+1确认落账) → DONE
 *   SUBMITTED → CANCELLED（仅 T 日 15:00 前可撤）
 *
 * 时间规则：
 *   - T 日 15:00 前提交的订单按 T 日净值成交，T+1 确认
 *   - 买入：T+1 份额确认，T+1 起计收益
 *   - 卖出：T+1 确认到账，收益计算至 T 日止
 */

const feeModule = require('./fee');

/**
 * 创建订单（SUBMITTED 状态，T 日下单）
 * @param {object} ctx { db, saveTransaction, updateHolding, getUserPortfolio }
 * @param {object} o { userId, fundCode, orderType(BUY/SELL), amount, price, shares(卖出时), reason }
 * @returns {Promise<object>} 订单记录
 */
// 本地日期 YYYY-MM-DD（交易日期以本地时区为准，避免 UTC 日期偏移）
function getLocalDateStr(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return y + '-' + m + '-' + day;
}

// A股休市日（工作日内的法定节假日，来源：engine/holidays.json，国务院办公厅 2026 年节假日通知）
let holidaySet = null;
function loadHolidays() {
  if (holidaySet) return;
  holidaySet = new Set();
  try {
    const h = require('./holidays.json');
    const year = String(new Date().getFullYear());
    (h[year] || []).forEach(d => holidaySet.add(d));
  } catch (e) {
    holidaySet = new Set();
  }
}

// 是否交易日：周一~周五 且 非节假日
function isTradingDay(now) {
  loadHolidays();
  const dow = now.getDay();
  if (dow === 0 || dow === 6) return false;
  return !holidaySet.has(getLocalDateStr(now));
}

// 是否处于交易时段：本地交易日 09:00:00 ~ 15:05:59 允许下单
// （15:00 整后提交按 T+1 净值确认，属真实基金规则；15:05 尾差为收盘分析容错）
function isTradingWindow(now) {
  if (!isTradingDay(now)) return false;
  const t = now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds();
  return t >= 9 * 3600 && t <= 15 * 3600 + 5 * 60 + 59;
}

async function createOrder(ctx, o) {
  const { db, audit } = ctx;
  const { userId, fundCode, orderType, amount, price, reason } = o;
  const nowD = new Date();

  // 硬校验：AI/任何来源都只能在交易时段创建订单，杜绝盘外交易
  if (!isTradingWindow(nowD)) {
    throw new Error('非交易时段禁止下单（仅本地工作日 09:00-15:05 可下单）');
  }

  const today = getLocalDateStr(nowD);

  const fees = await feeModule.getFundFees(db, fundCode);

  let fee = 0;
  let orderShares = 0;
  if (orderType === 'BUY') {
    fee = feeModule.calcBuyFee(amount, fees.buy_fee_pct);
    orderShares = Number(((amount - fee) / price).toFixed(4));
  } else if (orderType === 'SELL') {
    orderShares = o.shares || 0;
  } else {
    throw new Error(`不支持的订单类型: ${orderType}`);
  }

  // 真实基金规则：15:00 前（含盘中）下单按当日净值确认（T 日）；15:00 后下单按下一交易日净值确认（T+1 日）
  const h = nowD.getHours(), m = nowD.getMinutes();
  const afterCutoff = (h > 15) || (h === 15 && m >= 0);
  let tradeDate = today;
  if (afterCutoff) {
    const nxt = new Date(nowD);
    nxt.setDate(nxt.getDate() + 1);
    tradeDate = getLocalDateStr(nxt);
  }

  const order = {
    user_id: userId,
    fund_code: fundCode,
    order_type: orderType,
    amount: Number(amount.toFixed(2)),
    shares: orderShares,
    price: price,
    fee: fee,
    status: 'SUBMITTED',
    order_date: today,
    trade_date: tradeDate,
    reason: reason || '',
    created_at: nowD.toISOString()
  };

  return new Promise((resolve, reject) => {
    const sql = `INSERT INTO orders (user_id, fund_code, order_type, amount, shares, price, fee, status, order_date, trade_date, reason)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`;
    db.run(sql, [order.user_id, order.fund_code, order.order_type, order.amount, order.shares, order.price, order.fee, order.status, order.order_date, order.trade_date, order.reason], function (err) {
      if (err) return reject(err);
      order.id = this.lastID;
      if (audit) {
        audit('order-engine', 'CREATE_ORDER', `${userId} ${orderType} ${fundCode}`, { id: order.id, amount: order.amount, price: order.price, fee: order.fee });
      }
      resolve(order);
    });
  });
}

/**
 * 批量确认订单（T+1 确认落账，盘后任务调用）
 * @param {object} ctx { db, saveTransaction, updateHolding, audit }
 * @param {string} confirmDate 确认日期 YYYY-MM-DD（默认今天）
 * @returns {Promise<object>} { confirmed: number, errors: string[] }
 */
async function confirmPendingOrders(ctx, confirmDate) {
  const { db, saveTransaction, updateHolding, audit } = ctx;
  const date = confirmDate || new Date().toISOString().slice(0, 10);

  // T+1 确认：trade_date 严格早于今天 → 该 T 日净值已公布（盘后 21:30 已入库），可确认落账
  const orders = await new Promise((resolve, reject) => {
    db.all("SELECT * FROM orders WHERE status = 'SUBMITTED' AND trade_date < ? ORDER BY id", [date], (err, rows) => err ? reject(err) : resolve(rows));
  });

  const errors = [];
  let confirmed = 0;

  for (const order of orders) {
    try {
      // T+1 确认：成交净值必须取 T 日（trade_date）官方净值，而非下单时快照（净值当晚公布后以官方为准）
      const tNav = await new Promise((resolve) => {
        db.get('SELECT unit_nav FROM fund_nav WHERE fund_code = ? AND nav_date = ?', [order.fund_code, order.trade_date || order.order_date], (err, row) => resolve(err ? null : row));
      });
      const confirmPrice = tNav && tNav.unit_nav ? tNav.unit_nav : order.price;
      const holding = await getHolding(db, order.user_id, order.fund_code);
      if (order.order_type === 'BUY') {
        // 按 T 日净值确认份额（申购费按确认金额计提）
        const confirmShares = Number(((order.amount - order.fee) / confirmPrice).toFixed(4));
        // 合并持仓：成本 = 原成本 + 投入金额（含申购费，计入成本）；份额相加；成本价 = 总成本/总份额
        const newShares = Number(((holding ? holding.shares : 0) + confirmShares).toFixed(4));
        const newTotalCost = Number(((holding ? holding.total_cost : 0) + order.amount).toFixed(2));
        const newCostPrice = newShares > 0 ? Number((newTotalCost / newShares).toFixed(4)) : 0;
        await updateHolding(order.user_id, order.fund_code, newShares, newCostPrice, newTotalCost);
        await saveTransaction(order.user_id, {
          fund_code: order.fund_code,
          action: 'BUY',
          amount: order.amount,
          price: confirmPrice,
          shares: confirmShares,
          fees: order.fee,
          reason: order.reason || 'AI自动建仓（收盘信号）'
        });
        order.shares = confirmShares;
      } else if (order.order_type === 'SELL') {
        if (!holding || holding.shares <= 0) {
          throw new Error(`持仓为空，无法确认卖出 ${order.fund_code}`);
        }
        const sellShares = Math.min(order.shares, holding.shares);
        const redeemAmount = Number((sellShares * confirmPrice).toFixed(2));
        const fees = await feeModule.getFundFees(db, order.fund_code);
        // 先进先出（FIFO）分批赎回：从最早买入的份额开始扣，每批按各自持有天数算赎回费
        // 与真实基金一致（天天基金费率页注：赎回份额按先进先出算持有时间和对应赎回费用）
        const buyBatches = await new Promise((resolve, reject) => {
          db.all("SELECT id, shares, amount, price, transaction_date, remaining_shares FROM transactions WHERE user_id = ? AND fund_code = ? AND transaction_type = 'BUY' AND remaining_shares > 0 ORDER BY transaction_date ASC, id ASC",
            [order.user_id, order.fund_code], (err, rows) => err ? reject(err) : resolve(rows));
        });
        let toSell = sellShares;
        let sellFee = 0;
        let soldCost = 0;
        const batchNotes = [];
        for (const b of buyBatches) {
          if (toSell <= 0) break;
          const take = Math.min(toSell, b.remaining_shares);
          const batchAmount = Number((take * confirmPrice).toFixed(2));
          const holdDays = feeModule.calcHoldDays(b.transaction_date.slice(0, 10), date);
          const batchFee = feeModule.calcSellFee(batchAmount, holdDays, fees);
          sellFee = Number((sellFee + batchFee).toFixed(2));
          // 该批含费成本价 = 申购总额 / 申购份额（申购费计入成本）
          const batchCostPrice = Number((b.amount / b.shares).toFixed(4));
          soldCost = Number((soldCost + take * batchCostPrice).toFixed(2));
          batchNotes.push('买入' + b.transaction_date.slice(0, 10) + '持' + holdDays + '天×' + take + '份费率' + (batchFee / batchAmount * 100).toFixed(2) + '%');
          await new Promise((resolve, reject) => {
            db.run('UPDATE transactions SET remaining_shares = ROUND(remaining_shares - ?, 4) WHERE id = ?', [take, b.id], (err) => err ? reject(err) : resolve());
          });
          toSell = Number((toSell - take).toFixed(4));
        }
        if (toSell > 0) {
          throw new Error('可赎份额不足：' + order.fund_code + ' 需要 ' + sellShares + ' 份，实际可赎 ' + Number((sellShares - toSell).toFixed(4)) + ' 份');
        }
        const netProceeds = Number((redeemAmount - sellFee).toFixed(2));
        // 已实现盈亏 = 赎回净额 - 卖出成本（含赎回费影响，负值=亏损+费）
        const realized = Number((netProceeds - soldCost).toFixed(2));
        await new Promise((resolve, reject) => {
          db.run('INSERT INTO realized_pnl (user_id, fund_code, amount, sell_fee, note) VALUES (?, ?, ?, ?, ?)',
            [order.user_id, order.fund_code, realized, sellFee, '卖出确认 ' + order.order_date + ' FIFO: ' + batchNotes.join('；')], (err) => err ? reject(err) : resolve());
        });
        const remainShares = Number((holding.shares - sellShares).toFixed(4));
        if (remainShares <= 0.0001) {
          // 清仓
          await updateHolding(order.user_id, order.fund_code, 0, 0, 0);
        } else {
          const remainCost = Number((holding.total_cost - soldCost).toFixed(2));
          const remainPrice = Number((remainCost / remainShares).toFixed(4));
          await updateHolding(order.user_id, order.fund_code, remainShares, remainPrice, remainCost);
        }
        await saveTransaction(order.user_id, {
          fund_code: order.fund_code,
          action: 'SELL',
          amount: redeemAmount,
          price: confirmPrice,
          shares: sellShares,
          fees: sellFee,
          reason: (order.reason || 'AI自动退场') + '（FIFO: ' + batchNotes.join('；') + '）'
        });
      }

      await new Promise((resolve, reject) => {
        db.run("UPDATE orders SET status='DONE', confirm_date=?, fee=?, price=?, shares=? WHERE id=?",
          [date, order.fee, confirmPrice, order.shares, order.id], (err) => err ? reject(err) : resolve());
      });
      if (audit) {
        audit('order-engine', 'CONFIRM_ORDER', `${order.user_id} ${order.order_type} ${order.fund_code}`, { id: order.id, date });
      }
      confirmed++;
    } catch (e) {
      errors.push(`订单#${order.id} ${order.fund_code}: ${e.message}`);
    }
  }

  return { confirmed, errors };
}

/**
 * 读取持仓（orders 引擎内部用）
 */
function getHolding(db, userId, fundCode) {
  return new Promise((resolve) => {
    db.get('SELECT * FROM holdings WHERE user_id = ? AND fund_code = ?', [userId, fundCode], (err, row) => {
      if (err || !row || !row.shares) return resolve(null);
      resolve(row);
    });
  });
}

/**
 * 取消订单（仅 SUBMITTED 且当日可撤）
 * @returns {Promise<boolean>}
 */
function cancelOrder(db, orderId, userId) {
  return new Promise((resolve, reject) => {
    const today = getLocalDateStr(new Date());
    db.run("UPDATE orders SET status='CANCELLED' WHERE id=? AND user_id=? AND status='SUBMITTED' AND order_date=?",
      [orderId, userId, today], function (err) {
        if (err) return reject(err);
        resolve(this.changes > 0);
      });
  });
}

module.exports = { createOrder, confirmPendingOrders, cancelOrder, getHolding };
