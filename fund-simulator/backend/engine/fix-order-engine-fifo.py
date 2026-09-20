# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\engine\order-engine.js'
with io.open(p, 'r', encoding='utf-8') as f:
    c = f.read()

old = """        const sellShares = Math.min(order.shares, holding.shares);
        const redeemAmount = Number((sellShares * confirmPrice).toFixed(2));
        const fees = await feeModule.getFundFees(db, order.fund_code);
        // 持有天数：从该基金首次买入日算起（真实赎回费规则），而非卖出下单日
        const firstBuy = await new Promise((resolve) => {
          db.get("SELECT MIN(transaction_date) AS md FROM transactions WHERE user_id = ? AND fund_code = ? AND transaction_type = 'BUY'", [order.user_id, order.fund_code], (err, row) => resolve(err ? null : row));
        });
        const buyStart = (firstBuy && firstBuy.md) ? firstBuy.md.slice(0, 10) : order.order_date;
        const holdDays = feeModule.calcHoldDays(buyStart, date);
        const sellFee = feeModule.calcSellFee(redeemAmount, holdDays, fees);
        const netProceeds = Number((redeemAmount - sellFee).toFixed(2));
        // 卖出部分对应的持仓成本
        const soldCost = Number((holding.total_cost * (sellShares / holding.shares)).toFixed(2));
        // 已实现盈亏 = 赎回净额 - 卖出成本（含赎回费影响，负值=亏损+费）
        const realized = Number((netProceeds - soldCost).toFixed(2));
        await new Promise((resolve, reject) => {
          db.run('INSERT INTO realized_pnl (user_id, fund_code, amount, sell_fee, note) VALUES (?, ?, ?, ?, ?)',
            [order.user_id, order.fund_code, realized, sellFee, '卖出确认 ' + order.order_date], (err) => err ? reject(err) : resolve());
        });
        const remainShares = Number((holding.shares - sellShares).toFixed(4));
        if (remainShares <= 0.0001) {
          // 清仓
          await updateHolding(order.user_id, order.fund_code, 0, 0, 0);
        } else {
          const remainCost = Number((holding.total_cost * (remainShares / holding.shares)).toFixed(2));
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
          reason: order.reason || 'AI自动退场'
        });"""

new = """        const sellShares = Math.min(order.shares, holding.shares);
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
          batchNotes.push('\u4e70\u5165' + b.transaction_date.slice(0, 10) + '\u6301' + holdDays + '\u5929\u00d7' + take + '\u4efd\u8d39\u7387' + (batchFee / batchAmount * 100).toFixed(2) + '%');
          await new Promise((resolve, reject) => {
            db.run('UPDATE transactions SET remaining_shares = ROUND(remaining_shares - ?, 4) WHERE id = ?', [take, b.id], (err) => err ? reject(err) : resolve());
          });
          toSell = Number((toSell - take).toFixed(4));
        }
        if (toSell > 0) {
          throw new Error('\u53ef\u8d4e\u4efd\u989d\u4e0d\u8db3\uff1a' + order.fund_code + ' \u9700\u8981 ' + sellShares + ' \u4efd\uff0c\u5b9e\u9645\u53ef\u8d4e ' + Number((sellShares - toSell).toFixed(4)) + ' \u4efd');
        }
        const netProceeds = Number((redeemAmount - sellFee).toFixed(2));
        // 已实现盈亏 = 赎回净额 - 卖出成本（含赎回费影响，负值=亏损+费）
        const realized = Number((netProceeds - soldCost).toFixed(2));
        await new Promise((resolve, reject) => {
          db.run('INSERT INTO realized_pnl (user_id, fund_code, amount, sell_fee, note) VALUES (?, ?, ?, ?, ?)',
            [order.user_id, order.fund_code, realized, sellFee, '\u5356\u51fa\u786e\u8ba4 ' + order.order_date + ' FIFO: ' + batchNotes.join('\uff1b')], (err) => err ? reject(err) : resolve());
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
          reason: (order.reason || 'AI\u81ea\u52a8\u9000\u573a') + '\uff08FIFO: ' + batchNotes.join('\uff1b') + '\uff09'
        });"""

if old not in c:
    print('ERROR: anchor not found')
    raise SystemExit(1)
c = c.replace(old, new)
with io.open(p, 'w', encoding='utf-8', newline='') as f:
    f.write(c)
print('OK: order-engine.js SELL 改为 FIFO 分批赎回')
