/**
 * 费用引擎（真实基金费率口径，按基金单独配置）
 * 规格来源：fund/AI_FUND_OPERATIONS_DESIGN.md §6.2
 * 费率来源：fund_fees 表（天天基金 2026-09 各基金费率页）；无配置时使用默认值
 * 申购费：内扣法（前端收费）= 金额 - 金额/(1+费率)，与基金公司公式一致
 * 赎回费：按各基金真实赎回阶梯（持有天数从首次买入日起算）
 */

// 默认费率（与主流 A 类偏股/混合基金一致）
const DEFAULT_FEES = {
  buy_fee_pct: 0.0015,      // 申购费 0.15%（天天基金 1 折）
  sell_schedule: [          // 赎回阶梯（天数 → 费率），常见偏股混合 A 类
    { days: 7, rate: 0.015 },      // <7天 1.5%
    { days: 30, rate: 0.0075 },    // 7-29天 0.75%
    { days: 365, rate: 0.005 },    // 30-364天 0.5%
    { days: 730, rate: 0.0025 },   // 365-729天 0.25%
    { days: Infinity, rate: 0 }    // >=730天 0
  ],
  manage_fee_pct: 0.012,    // 管理费年化 1.2%（逐日计提，计入净值，不另行支付）
  custody_fee_pct: 0.002,   // 托管费年化 0.2%
  service_fee_pct: 0        // 销售服务费（A类无）
};

// 各基金真实费率（天天基金 2026-09 费率页）：
// 005827 易方达蓝筹精选混合：申购 1.5%→1折0.15%；赎回 <7d 1.5% / 7-29d 0.75% / 30-364d 0.5% / 365-729d 0.25% / >=730d 0；管理1.2% 托管0.2%
// 161725 招商中证白酒指数(LOF)A：申购 1.0%→1折0.10%；赎回 <7d 1.5% / 7-364d 0.5% / >=365d 0.25%；管理1.0% 托管0.22%
// 000001 华夏成长混合：申购 1.5%→1折0.15%；赎回 <7d 1.5% / >=7d 0.5%（两档）；管理1.2% 托管0.2%
// 005267 嘉实价值精选股票A：申购 1.5%→1折0.15%；赎回 <7d 1.5% / 7-29d 0.75% / 30-364d 0.5% / 365-729d 0.25% / >=730d 0；管理1.2% 托管0.2%
const FUND_FEES = {
  '005827': {
    buy_fee_pct: 0.0015,
    sell_schedule: [
      { days: 7, rate: 0.015 },
      { days: 30, rate: 0.0075 },
      { days: 365, rate: 0.005 },
      { days: 730, rate: 0.0025 },
      { days: Infinity, rate: 0 }
    ],
    manage_fee_pct: 0.012, custody_fee_pct: 0.002, service_fee_pct: 0
  },
  '161725': {
    buy_fee_pct: 0.001,
    sell_schedule: [
      { days: 7, rate: 0.015 },
      { days: 365, rate: 0.005 },
      { days: Infinity, rate: 0.0025 }
    ],
    manage_fee_pct: 0.01, custody_fee_pct: 0.0022, service_fee_pct: 0
  },
  '000001': {
    buy_fee_pct: 0.0015,
    sell_schedule: [
      { days: 7, rate: 0.015 },
      { days: Infinity, rate: 0.005 }
    ],
    manage_fee_pct: 0.012, custody_fee_pct: 0.002, service_fee_pct: 0
  },
  '005267': {
    buy_fee_pct: 0.0015,
    sell_schedule: [
      { days: 7, rate: 0.015 },
      { days: 30, rate: 0.0075 },
      { days: 365, rate: 0.005 },
      { days: 730, rate: 0.0025 },
      { days: Infinity, rate: 0 }
    ],
    manage_fee_pct: 0.012, custody_fee_pct: 0.002, service_fee_pct: 0
  }
};

/**
 * 获取基金费率配置（优先 DB fund_fees 表，其次内置真实费率表，缺省用默认）
 */
function getFundFees(db, fundCode) {
  return new Promise((resolve) => {
    db.get('SELECT * FROM fund_fees WHERE fund_code = ?', [fundCode], (err, row) => {
      if (err || !row) {
        resolve({ ...(FUND_FEES[fundCode] || DEFAULT_FEES) });
        return;
      }
      let schedule;
      if (row.sell_schedule) {
        try { schedule = JSON.parse(row.sell_schedule); } catch (e) { schedule = null; }
      }
      resolve({
        buy_fee_pct: row.buy_fee_pct ?? (FUND_FEES[fundCode] || DEFAULT_FEES).buy_fee_pct,
        sell_schedule: schedule || (FUND_FEES[fundCode] || DEFAULT_FEES).sell_schedule,
        sell_fee_7d: row.sell_fee_7d ?? null,
        sell_fee_1y: row.sell_fee_1y ?? null,
        sell_fee_ge1y: row.sell_fee_ge1y ?? null,
        manage_fee_pct: row.manage_fee_pct ?? (FUND_FEES[fundCode] || DEFAULT_FEES).manage_fee_pct,
        custody_fee_pct: row.custody_fee_pct ?? (FUND_FEES[fundCode] || DEFAULT_FEES).custody_fee_pct,
        service_fee_pct: row.service_fee_pct ?? (FUND_FEES[fundCode] || DEFAULT_FEES).service_fee_pct
      });
    });
  });
}

/**
 * 计算申购费（内扣法，与基金公司公式一致）：申购费 = 金额 - 金额/(1+费率)
 * 净申购金额 = 金额/(1+费率)，申购费 = 金额 - 净申购金额
 */
function calcBuyFee(amount, buyFeePct) {
  const net = amount / (1 + buyFeePct);
  return Number((amount - net).toFixed(2));
}

/**
 * 计算赎回费：按持有天数匹配该基金赎回阶梯
 * @param {number} redeemAmount 赎回金额（份额 × 净值）
 * @param {number} holdDays 持有天数（自然日，从首次买入日算）
 * @param {object} fees 费率对象（含 sell_schedule）
 */
function calcSellFee(redeemAmount, holdDays, fees) {
  const schedule = fees.sell_schedule || [
    { days: 7, rate: fees.sell_fee_7d ?? 0.015 },
    { days: 365, rate: fees.sell_fee_1y ?? 0.005 },
    { days: Infinity, rate: fees.sell_fee_ge1y ?? 0.0025 }
  ];
  let pct = schedule[schedule.length - 1].rate;
  for (const s of schedule) {
    if (holdDays < s.days) { pct = s.rate; break; }
  }
  return Number((redeemAmount * pct).toFixed(2));
}

/**
 * 计算持有天数（自然日，从持仓首次买入日算）
 */
function calcHoldDays(buyDate, nowDate) {
  const d1 = new Date(buyDate + 'T00:00:00');
  const d2 = new Date(nowDate + 'T00:00:00');
  return Math.max(0, Math.floor((d2 - d1) / 86400000));
}

/**
 * 计算单日计提费用（管理费+托管费+销售服务费，逐日计提，计入净值）
 */
function calcDailyAccrual(marketValue, fees) {
  const annual = fees.manage_fee_pct + fees.custody_fee_pct + fees.service_fee_pct;
  return Number((marketValue * annual / 365).toFixed(4));
}

module.exports = {
  DEFAULT_FEES,
  FUND_FEES,
  getFundFees,
  calcBuyFee,
  calcSellFee,
  calcHoldDays,
  calcDailyAccrual
};
