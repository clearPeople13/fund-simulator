import io

# 1) readonly.js 加 /ai/fund-fees
p1 = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\routes\readonly.js"
with io.open(p1, 'r', encoding='utf-8') as f:
    s1 = f.read()
old = "  r.get('/ai/fund-daily-pnl', async (req, res) => {"
new = """  r.get('/ai/fund-fees', async (req, res) => {
    try {
      const fundCode = req.query.fund_code;
      if (!fundCode) return res.status(400).json({ error: 'fund_code required' });
      const fee = await new Promise((resolve) => db.get('SELECT * FROM fund_fees WHERE fund_code = ?', [fundCode], (e, r) => resolve(r || null)));
      if (!fee) return res.json({ fund_code: fundCode, found: false });
      let schedule = [];
      try { schedule = JSON.parse(fee.sell_schedule || '[]'); } catch (e) { schedule = []; }
      const pct = v => v == null ? null : (v * 100);
      res.json({
        fund_code: fundCode, found: true,
        buy_fee_pct: pct(fee.buy_fee_pct),
        manage_fee_pct: pct(fee.manage_fee_pct),
        custody_fee_pct: pct(fee.custody_fee_pct),
        service_fee_pct: pct(fee.service_fee_pct),
        sell_schedule: schedule.map(x => ({ days: x.days, rate_pct: Math.round(x.rate * 10000) / 100 })),
        updated_at: fee.updated_at
      });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.get('/ai/fund-daily-pnl', async (req, res) => {"""
assert s1.count(old) == 1
s1 = s1.replace(old, new)
with io.open(p1, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s1)

# 2) server.js 删 /api/ai/fund-fees 块
p2 = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p2, 'r', encoding='utf-8') as f:
    s2 = f.read()
old2 = """// ===== 单基金费率（申购/赎回阶梯/管理/托管，真实 fund_fees）=====
app.get('/api/ai/fund-fees', async (req, res) => {
  try {
    const fundCode = req.query.fund_code;
    if (!fundCode) return res.status(400).json({ error: 'fund_code required' });
    const fee = await new Promise((resolve) => db.get('SELECT * FROM fund_fees WHERE fund_code = ?', [fundCode], (e, r) => resolve(r || null)));
    if (!fee) return res.json({ fund_code: fundCode, found: false });
    let schedule = [];
    try { schedule = JSON.parse(fee.sell_schedule || '[]'); } catch (e) { schedule = []; }
    const pct = v => v == null ? null : (v * 100);
    res.json({
      fund_code: fundCode, found: true,
      buy_fee_pct: pct(fee.buy_fee_pct),
      manage_fee_pct: pct(fee.manage_fee_pct),
      custody_fee_pct: pct(fee.custody_fee_pct),
      service_fee_pct: pct(fee.service_fee_pct),
      sell_schedule: schedule.map(x => ({ days: x.days, rate_pct: Math.round(x.rate * 10000) / 100 })),
      updated_at: fee.updated_at
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

"""
assert s2.count(old2) == 1
s2 = s2.replace(old2, '// /api/ai/fund-fees 已抽到 routes/readonly.js\n')
with io.open(p2, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s2)
print('fund-fees moved')
