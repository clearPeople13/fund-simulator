# -*- coding: utf-8 -*-
"""后端新增 /api/ai/fees：费用统计（summary + by_fund + detail 逐笔含费率）"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

anchor = """// 获取AI交易记录
app.get('/api/ai/transactions', async (req, res) => {"""
api = """// 费用统计：汇总 + 按基金分组 + 逐笔明细（含费率，可追溯每笔组成）
app.get('/api/ai/fees', async (req, res) => {
  try {
    const userId = req.query.user_id || currentUser;
    const rows = await new Promise((resolve, reject) => {
      db.all(`SELECT t.id, t.transaction_date, t.fund_code, t.transaction_type, t.amount, t.price, t.shares, t.fees,
              COALESCE(f.fund_name, t.fund_code) AS fund_name
              FROM transactions t LEFT JOIN funds f ON f.fund_code = t.fund_code
              WHERE t.user_id = ? ORDER BY t.transaction_date ASC, t.id ASC`, [userId], (err, r) => err ? reject(err) : resolve(r || []));
    });
    const round2 = v => Math.round(v * 100) / 100;
    const detail = rows.map(t => ({
      id: t.id,
      transaction_date: t.transaction_date,
      fund_code: t.fund_code,
      fund_name: t.fund_name,
      transaction_type: t.transaction_type,
      amount: t.amount,
      shares: t.shares,
      price: t.price,
      fees: round2(t.fees || 0),
      // 费率口径：申购费/赎回费 = fees / 交易金额（内扣法，实际扣款=amount）
      rate: t.amount > 0 ? Number((((t.fees || 0) / t.amount) * 100).toFixed(4)) : 0
    }));
    let buy_fee = 0, sell_fee = 0;
    const byFund = {};
    rows.forEach(t => {
      const f = t.fees || 0;
      if (t.transaction_type === 'BUY') buy_fee += f; else if (t.transaction_type === 'SELL') sell_fee += f;
      if (!byFund[t.fund_code]) byFund[t.fund_code] = { fund_code: t.fund_code, fund_name: t.fund_name, buy_fee: 0, sell_fee: 0, buy_count: 0, sell_count: 0, buy_amount: 0, sell_amount: 0 };
      const g = byFund[t.fund_code];
      if (t.transaction_type === 'BUY') { g.buy_fee += f; g.buy_count++; g.buy_amount += t.amount; }
      else if (t.transaction_type === 'SELL') { g.sell_fee += f; g.sell_count++; g.sell_amount += t.amount; }
    });
    const by_fund = Object.values(byFund).map(g => ({
      ...g,
      buy_fee: round2(g.buy_fee), sell_fee: round2(g.sell_fee),
      total_fee: round2(g.buy_fee + g.sell_fee),
      buy_rate: g.buy_amount > 0 ? Number(((g.buy_fee / g.buy_amount) * 100).toFixed(4)) : 0,
      sell_rate: g.sell_amount > 0 ? Number(((g.sell_fee / g.sell_amount) * 100).toFixed(4)) : 0
    }));
    res.json({
      user_id: userId,
      summary: { buy_fee: round2(buy_fee), sell_fee: round2(sell_fee), total_fee: round2(buy_fee + sell_fee), trade_count: rows.length },
      by_fund,
      detail
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 获取AI交易记录
app.get('/api/ai/transactions', async (req, res) => {"""
assert s.count(anchor) == 1, 'anchor not found'
s = s.replace(anchor, api)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('server.js patched')
