# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\engine\order-engine.js'
c = io.open(p, encoding='utf-8').read()

# 1. createOrder：计算 trade_date（本地时间 <15:00 → 当日净值确认；>=15:00 → 次日净值确认，真实基金申购规则）
old = """  const order = {
    user_id: userId,
    fund_code: fundCode,
    order_type: orderType,
    amount: Number(amount.toFixed(2)),
    shares: orderShares,
    price: price,
    fee: fee,
    status: 'SUBMITTED',
    order_date: today,
    reason: reason || '',
    created_at: new Date().toISOString()
  };

  return new Promise((resolve, reject) => {
    const sql = `INSERT INTO orders (user_id, fund_code, order_type, amount, shares, price, fee, status, order_date, reason)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`;
    db.run(sql, [order.user_id, order.fund_code, order.order_type, order.amount, order.shares, order.price, order.fee, order.status, order.order_date, order.reason], function (err) {"""
new = """  // 真实基金规则：15:00 前（含盘中）下单按当日净值确认（T 日）；15:00 后下单按下一交易日净值确认（T+1 日）
  const nowD = new Date();
  const h = nowD.getHours(), m = nowD.getMinutes();
  const afterCutoff = (h > 15) || (h === 15 && m >= 0);
  let tradeDate = today;
  if (afterCutoff) {
    const nxt = new Date(nowD);
    nxt.setDate(nxt.getDate() + 1);
    tradeDate = nxt.getFullYear() + '-' + String(nxt.getMonth() + 1).padStart(2, '0') + '-' + String(nxt.getDate()).padStart(2, '0');
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
    db.run(sql, [order.user_id, order.fund_code, order.order_type, order.amount, order.shares, order.price, order.fee, order.status, order.order_date, order.trade_date, order.reason], function (err) {"""
assert c.count(old) == 1, 'createOrder %d' % c.count(old)
c = c.replace(old, new, 1)

# 2. confirmPendingOrders：只确认 T 日净值已公布的订单（trade_date < 今天），成交净值取 trade_date 官方净值
old2 = """  const orders = await new Promise((resolve, reject) => {
    db.all("SELECT * FROM orders WHERE status = 'SUBMITTED' AND order_date < ? ORDER BY id", [date], (err, rows) => err ? reject(err) : resolve(rows));
  });"""
new2 = """  // T+1 确认：trade_date 严格早于今天 → 该 T 日净值已公布（盘后 21:30 已入库），可确认落账
  const orders = await new Promise((resolve, reject) => {
    db.all("SELECT * FROM orders WHERE status = 'SUBMITTED' AND trade_date < ? ORDER BY id", [date], (err, rows) => err ? reject(err) : resolve(rows));
  });"""
assert c.count(old2) == 1, 'confirm q %d' % c.count(old2)
c = c.replace(old2, new2, 1)

old3 = """      // T+1 确认：成交净值必须取 T 日（下单日）净值，而非下单时快照（净值当晚公布后以官方为准）
      const tNav = await new Promise((resolve) => {
        db.get('SELECT unit_nav FROM fund_nav WHERE fund_code = ? AND nav_date = ?', [order.fund_code, order.order_date], (err, row) => resolve(err ? null : row));
      });"""
new3 = """      // T+1 确认：成交净值必须取 T 日（trade_date）官方净值，而非下单时快照（净值当晚公布后以官方为准）
      const tNav = await new Promise((resolve) => {
        db.get('SELECT unit_nav FROM fund_nav WHERE fund_code = ? AND nav_date = ?', [order.fund_code, order.trade_date || order.order_date], (err, row) => resolve(err ? null : row));
      });"""
assert c.count(old3) == 1, 'tNav %d' % c.count(old3)
c = c.replace(old3, new3, 1)

io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('engine OK')
