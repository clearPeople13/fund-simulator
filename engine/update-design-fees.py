# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\AI_FUND_OPERATIONS_DESIGN.md'
with io.open(p, 'r', encoding='utf-8') as f:
    c = f.read()

old = """### 6.2 费用口径（真实基金规则）
| 费用 | 规则 | 记账 |
|---|---|---|
| 申购费 | 前端费率（默认 0.15%，按 fund_fees） | 买入时从现金扣除 |
| 赎回费 | 持有 <7 天 1.5%；<1 年 0.5%；≥1 年 0.25% 或 0 | 卖出时从到账金额扣除 |
| 管理费 | 年化（默认 1.5%）逐日计提 | 每日从该基金市值计提，计入成本 |
| 托管费 | 年化（默认 0.25%）逐日计提 | 同上 |
| 销售服务费 | C 类（默认 0.4%/年）逐日计提 | 同上 |

费用流水写入 orders.fee 与每日计提日志（fees_accrued 并入 performance 计算）。"""

new = """### 6.2 费用口径（真实基金规则，2026-09-18 更新）
**费率来源**：天天基金各基金费率页（fundf10.eastmoney.com/jjfl_<code>.html），按基金单独配置 fund_fees 表 / fee.js FUND_FEES；新基金必须查真实费率，不得沿用默认。

| 基金 | 申购费(1折) | 赎回阶梯 | 管理/托管 |
|---|---|---|---|
| 005827 易方达蓝筹精选混合 | 0.15% | <7d 1.5% / 7-29d 0.75% / 30-364d 0.5% / 365-729d 0.25% / ≥730d 0 | 1.2% / 0.2% |
| 161725 招商中证白酒(LOF)A | 0.10% | <7d 1.5% / 7-364d 0.5% / ≥365d 0.25% | 1.0% / 0.22% |
| 000001 华夏成长混合 | 0.15% | <7d 1.5% / ≥7d 0.5% | 1.2% / 0.2% |
| 005267 嘉实价值精选股票A | 0.15% | <7d 1.5% / 7-29d 0.75% / 30-364d 0.5% / 365-729d 0.25% / ≥730d 0 | 1.2% / 0.2% |

| 费用 | 规则 | 记账 |
|---|---|---|
| 申购费 | 前端收费，**内扣法**：申购费 = 金额 − 金额/(1+费率)；净申购额 = 金额/(1+费率)；份额 = 净额/净值 | 申购费计入持仓成本（成本价 = 申购总额/份额） |
| 赎回费 | **先进先出（FIFO）分批**：卖出从最早买入批次扣减，每批按各自持有天数查该基金阶梯，赎回费 = Σ(批金额×批费率)；持有天数从各批买入日起算 | 卖出时从到账金额扣除（净额入账） |
| 管理费 | 年化（按 fund_fees）逐日计提 | 每日从该基金市值计提，计入净值（不另行支付） |
| 托管费 | 年化（按 fund_fees）逐日计提 | 同上 |
| 销售服务费 | C 类按 fund_fees（A 类为 0）逐日计提 | 同上 |

- 卖出成本按批次含费成本价（amount/shares）累计；已实现盈亏 = 赎回净额 − 卖出成本
- transactions 表含 remaining_shares（每笔 BUY 剩余可赎份额），SELL 确认逐批扣减，FIFO 明细写入 realized_pnl.note
- 费用流水写入 orders.fee 与每日计提日志（fees_accrued 并入 performance 计算）。"""

if old not in c:
    print('ERROR: anchor not found')
    raise SystemExit(1)
c = c.replace(old, new)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c)
print('OK: AI_FUND_OPERATIONS_DESIGN.md §6.2 已更新为真实费率 + FIFO 规则')
