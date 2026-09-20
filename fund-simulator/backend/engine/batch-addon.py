# -*- coding: utf-8 -*-
"""真实分批建仓：已持有且信号仍 buy/add → 冷却期后按 add_ratio 分批加仓，单基金上限由风控兜底"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# ---- 1) default 配置加冷却期 ----
old1 = """    buy_ratio: 0.2, add_ratio: 0.1,  // 建仓/加仓比例"""
new1 = """    buy_ratio: 0.2, add_ratio: 0.1,  // 建仓/加仓比例
    add_cooldown_days: 5,        // 分批加仓冷却期（天）：距上次确认买入满 N 天才可再加仓"""
assert s.count(old1) == 1, 'default cfg not found'
s = s.replace(old1, new1)

# ---- 2) aggressive 配置加冷却期（更激进：3 天）----
old2 = """    buy_ratio: 0.2, add_ratio: 0.1,
    rebalance_frequency: 'weekly',"""
new2 = """    buy_ratio: 0.2, add_ratio: 0.1,
    add_cooldown_days: 3,        // 分批加仓冷却期（天）：激进用户加仓节奏更快
    rebalance_frequency: 'weekly',"""
assert s.count(old2) == 1, 'aggressive cfg not found'
s = s.replace(old2, new2)

# ---- 3) 买入分支重构：未持有=建仓；已持有=冷却期后分批加仓 ----
old3 = """            if (pendingBuy > 0) {
              console.log(`  → ${fundCode} 已有待确认买单，跳过重复下单`);
            } else if (!hasHolding2) {
              const ratio2 = action === 'buy' ? (userCfg.buy_ratio || 0.2) : (userCfg.add_ratio || 0.1);
              // 市场温度系数（frozen 0.5 / cold 0.8 / warm 1.1 / hot 1.2）调节建仓金额
              const tempRow2 = await new Promise((resolve) => {
                db.get('SELECT temperature FROM market_env ORDER BY date DESC LIMIT 1', [], (err, row) => resolve(err ? null : row));
              });
              const tempFactor2 = temperatureFactor(tempRow2 ? tempRow2.temperature : 'neutral');
              const suggestAmount2 = Math.round(portfolio.current_capital * ratio2 * tempFactor2);
              if (suggestAmount2 >= 100) {
                const rc = await checkRiskControls(userId, portfolio, 'BUY', fundCode, suggestAmount2, userCfg);
                if (!rc.pass) {
                  logRiskEvent(userId, 'BUY_BLOCKED', fundCode, rc.reason, 'block');
                  console.log(`  → 风控拦截买入 ${fundCode}: ${rc.reason}`);
                } else {
                  const order = await orderEngine.createOrder({ db, audit }, {
                    userId, fundCode, orderType: 'BUY', amount: suggestAmount2, price: currentNav,
                    reason: `AI自动建仓：${sig.signal.label}（${sig.signal.reason}）`
                  });
                  console.log(`  → 生成买入订单#${order.id} ${fundCode} ¥${suggestAmount2}（T+1确认）`);
                }
              } else {
                console.log(`  → ${fundCode} 可用现金不足（¥${portfolio.current_capital}），跳过下单`);
              }
            }"""

new3 = """            if (pendingBuy > 0) {
              console.log(`  → ${fundCode} 已有待确认买单，跳过重复下单`);
            } else {
              // 市场温度系数（frozen 0.5 / cold 0.8 / warm 1.1 / hot 1.2）调节建仓/加仓金额
              const tempRow2 = await new Promise((resolve) => {
                db.get('SELECT temperature FROM market_env ORDER BY date DESC LIMIT 1', [], (err, row) => resolve(err ? null : row));
              });
              const tempFactor2 = temperatureFactor(tempRow2 ? tempRow2.temperature : 'neutral');

              if (!hasHolding2) {
                // ===== 首笔建仓（未持有）：buy 分批建仓 20%，add 轻仓试探 10% =====
                const ratio2 = action === 'buy' ? (userCfg.buy_ratio || 0.2) : (userCfg.add_ratio || 0.1);
                const suggestAmount2 = Math.round(portfolio.current_capital * ratio2 * tempFactor2);
                if (suggestAmount2 >= 100) {
                  const rc = await checkRiskControls(userId, portfolio, 'BUY', fundCode, suggestAmount2, userCfg);
                  if (!rc.pass) {
                    logRiskEvent(userId, 'BUY_BLOCKED', fundCode, rc.reason, 'block');
                    console.log(`  → 风控拦截买入 ${fundCode}: ${rc.reason}`);
                  } else {
                    const order = await orderEngine.createOrder({ db, audit }, {
                      userId, fundCode, orderType: 'BUY', amount: suggestAmount2, price: currentNav,
                      reason: `AI自动建仓：${sig.signal.label}（${sig.signal.reason}）`
                    });
                    console.log(`  → 生成建仓订单#${order.id} ${fundCode} ¥${suggestAmount2}（T+1确认）`);
                  }
                } else {
                  console.log(`  → ${fundCode} 可用现金不足（¥${portfolio.current_capital}），跳过建仓`);
                }
              } else {
                // ===== 已持有 → 分批加仓（真实分批建仓：回调企稳信号下分批加仓）=====
                // 加仓节奏：距上次确认买入 >= add_cooldown_days 天才允许再加仓，避免越加越重；
                // 单基金总仓位上限（max_single_fund）由 checkRiskControls 兜底
                const lastBuyRow = await new Promise((resolve) => {
                  db.get("SELECT MAX(transaction_date) md FROM transactions WHERE user_id=? AND fund_code=? AND transaction_type='BUY'",
                    [userId, fundCode], (err, row) => resolve(err ? null : row));
                });
                const cooldown = userCfg.add_cooldown_days || 5;
                let daysSince = 9999;
                if (lastBuyRow && lastBuyRow.md) {
                  const lastD = new Date(utcToLocalStr(lastBuyRow.md).slice(0, 10) + 'T00:00:00');
                  const todayD = new Date(getLocalDateStr(new Date()) + 'T00:00:00');
                  daysSince = Math.round((todayD.getTime() - lastD.getTime()) / 86400000);
                }
                if (daysSince < cooldown) {
                  console.log(`  → ${fundCode} 距上次加仓 ${daysSince} 天 < 冷却期 ${cooldown} 天，暂不加仓（分批节奏）`);
                } else {
                  const addAmount = Math.round(portfolio.current_capital * (userCfg.add_ratio || 0.1) * tempFactor2);
                  if (addAmount >= 100) {
                    const rc = await checkRiskControls(userId, portfolio, 'BUY', fundCode, addAmount, userCfg);
                    if (!rc.pass) {
                      logRiskEvent(userId, 'BUY_BLOCKED', fundCode, rc.reason, 'block');
                      console.log(`  → 风控拦截加仓 ${fundCode}: ${rc.reason}`);
                    } else {
                      const order = await orderEngine.createOrder({ db, audit }, {
                        userId, fundCode, orderType: 'BUY', amount: addAmount, price: currentNav,
                        reason: `AI自动加仓（分批建仓）：${sig.signal.label}（${sig.signal.reason}）`
                      });
                      console.log(`  → 生成加仓订单#${order.id} ${fundCode} ¥${addAmount}（T+1确认，分批加仓）`);
                    }
                  } else {
                    console.log(`  → ${fundCode} 可用现金不足（¥${portfolio.current_capital}），跳过加仓`);
                  }
                }
              }
            }"""

assert s.count(old3) == 1, 'buy branch not found'
s = s.replace(old3, new3)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('patched server.js (batch add-on)')
