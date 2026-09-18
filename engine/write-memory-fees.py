# -*- coding: utf-8 -*-
import io, datetime

today = datetime.date.today().isoformat()
mem_path = r'C:\Users\jiancent\WorkBuddy\fund\.workbuddy\memory\2026-09-18.md'
try:
    with io.open(mem_path, 'r', encoding='utf-8') as f:
        old = f.read()
except IOError:
    old = ''

block = """

---
## 2026-09-18 手续费真实化（用户验收第二轮：持有天数 bug + 历史校准 + 每基金真实费率 + FIFO 分批赎回）

**1. 赎回费持有天数 bug 修复**
- 根因：order-engine 用【卖出下单日】算持有天数 → 永远 1 天 → 永远收 1.5%
- 修复：从该基金【首次买入日】起算 → 阶梯正确（200 天→0.5% ¥50、400 天→0.25% ¥25）

**2. 手续费校准重建（两轮）**
- 第一轮（统一 0.15% 口径）：历史 3 笔买入（005827/161725/005267）漏扣申购费 → 补费 30/30/24、份额/成本/realized 重建，realized -165.02、现金 81851.22/64001.82
- 第二轮（真实费率）：fund_fees 表按天天基金 2026-09 各基金费率页逐个配置；备份 fund_simulator.db.bak-20260918-fees / .bak-20260918-real-fees

**3. 每只基金真实费率（fund_fees 表 + fee.js FUND_FEES，来源=天天基金 jjfl_<code>.html，1 折优惠口径）**
| 基金 | 申购费 | 赎回阶梯 | 管理/托管 |
|---|---|---|---|
| 005827 易方达蓝筹精选 | 0.15% | <7d 1.5% / 7-29d 0.75% / 30-364d 0.5% / 365-729d 0.25% / ≥730d 0 | 1.2% / 0.2% |
| 161725 招商中证白酒(LOF)A | 0.10% | <7d 1.5% / 7-364d 0.5% / ≥365d 0.25% | 1.0% / 0.22% |
| 000001 华夏成长混合 | 0.15% | <7d 1.5% / ≥7d 0.5%（仅两档） | 1.2% / 0.2% |
| 005267 嘉实价值精选A | 0.15% | <7d 1.5% / 7-29d 0.75% / 30-364d 0.5% / 365-729d 0.25% / ≥730d 0 | 1.2% / 0.2% |

- 申购费【内扣法】（基金公司公式）：申购费 = 金额 − 金额/(1+费率)；净申购额 = 金额/(1+费率)；份额 = 净额/净值；申购费计入持仓成本
- 新基金费率须查天天基金费率页配置 fund_fees，不得沿用默认

**4. 赎回费先进先出（FIFO）分批（真实基金规则）**
- 卖出时从【最早买入批次】扣减份额，每批按各自持有天数查该基金赎回阶梯，赎回费 = Σ(批金额×批费率)；卖出成本 = Σ(批份额×该批含费成本价 amount/shares)
- transactions 新增 remaining_shares 列（每笔 BUY 剩余可赎份额）；SELL 确认逐批扣减；FIFO 明细写入 realized_pnl.note 与 transactions.reason（可审计）
- 测试：30 天前买 1w + 2 天前加仓 5k + 卖 7000 份 → 赎回费 62.26 = 6656.68份×0.5% + 343.32份×1.5%（而非统一费率）
- 引擎文件：engine/fee.js（DEFAULT_FEES/FUND_FEES/getFundFees/calcBuyFee/calcSellFee/calcHoldDays/calcDailyAccrual）、engine/order-engine.js（createOrder/confirmPendingOrders/cancelOrder/getHolding）；saveTransaction 在 server.js，BUY 写入 remaining_shares=shares

**5. 验收数值（校准后基准）**
- transactions：005827 BUY 费 29.95 份 13412.8831；161725 BUY 费 19.98 份 37847.1519；005267 BUY 费 23.96 份 7097.3549；000001 BUY 费 11.98 份 6163.5957；005827 SELL 费 150（持有2天<7d）
- holdings：default 005827 6695.8831 份 成本 1.491 总成本 9983.78；000001 6163.5957 份 1.2979；aggressive 161725 37847.1519 份 0.5284、005267 7097.3549 份 2.2542
- realized_pnl：005827 卖出 -165.00（净额 9850.27 − 含费成本 10015.27，FIFO 单批）；现金 default 81851.22 / aggressive 64001.82
- 激进 18 号 SUBMITTED：161725 SELL 18943 份（19 号确认，FIFO 持有 3 天→1.5%）、000001 BUY 6400（申购 0.15% 内扣 9.58）——正常 AI 操盘勿动
"""

with io.open(mem_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(old + block)
print('记忆已追加到', mem_path)
