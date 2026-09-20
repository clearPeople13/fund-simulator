import io

# 1) readonly.js 加 /ai/fees
p1 = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\routes\readonly.js"
with io.open(p1, 'r', encoding='utf-8') as f:
    s1 = f.read()
old = "  r.get('/market/overview', async (req, res) => {"
new = """  r.get('/ai/fees', async (req, res) => {
    try {
      const userId = req.query.user_id || getCurrentUser();
      const rows = await new Promise((resolve, reject) => {
        db.all(`SELECT t.id, t.transaction_date, t.fund_code, t.transaction_type, t.amount, t.price, t.shares, t.fees,
                COALESCE(f.fund_name, t.fund_code) AS fund_name
                FROM transactions t LEFT JOIN funds f ON f.fund_code = t.fund_code
                WHERE t.user_id = ? ORDER BY t.transaction_date ASC, t.id ASC`, [userId], (e, r) => e ? reject(e) : resolve(r || []));
      });
      const round2 = v => Math.round(v * 100) / 100;
      const detail = rows.map(t => ({
        id: t.id, transaction_date: t.transaction_date, fund_code: t.fund_code,
        fund_name: t.fund_name, transaction_type: t.transaction_type, amount: t.amount,
        shares: t.shares, price: t.price, fees: round2(t.fees || 0),
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
        ...g, buy_fee: round2(g.buy_fee), sell_fee: round2(g.sell_fee),
        total_fee: round2(g.buy_fee + g.sell_fee),
        buy_rate: g.buy_amount > 0 ? Number(((g.buy_fee / g.buy_amount) * 100).toFixed(4)) : 0,
        sell_rate: g.sell_amount > 0 ? Number(((g.sell_fee / g.sell_amount) * 100).toFixed(4)) : 0
      }));
      res.json({
        user_id: userId,
        summary: { buy_fee: round2(buy_fee), sell_fee: round2(sell_fee), total_fee: round2(buy_fee + sell_fee), trade_count: rows.length },
        by_fund, detail
      });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.get('/market/overview', async (req, res) => {"""
assert s1.count(old) == 1
s1 = s1.replace(old, new)
with io.open(p1, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s1)

# 2) server.js 删 /api/ai/fees 块
p2 = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p2, 'r', encoding='utf-8') as f:
    s2 = f.read()
start = s2.find("// 费用统计：汇总 + 按基金分组 + 逐笔明细")
assert start != -1
end = s2.find("// 单基金每日收益明细", start)
assert end != -1
s2 = s2[:start] + "// /api/ai/fees 已抽到 routes/readonly.js\n" + s2[end:]
with io.open(p2, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s2)
print('ai/fees moved')
