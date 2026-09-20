# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js'
c = io.open(p, encoding='utf-8').read()

# 手动添加自选：兼容全市场基金库（funds 表无则查 fund_universe，入库并拉净值）
old = """  try {
    // 校验基金是否在库中
    const fund = await new Promise((resolve, reject) => {
      db.get('SELECT fund_code FROM funds WHERE fund_code = ?', [fund_code], (err, row) => {
        if (err) reject(err); else resolve(row);
      });
    });
    if (!fund) return res.status(404).json({ error: `基金 ${fund_code} 不在基金库中` });

    await new Promise((resolve, reject) => {"""
new = """  try {
    // 校验基金：优先系统跟踪库 funds；不在则查全市场基金库 fund_universe，自动入库并拉取历史净值
    let fund = await new Promise((resolve, reject) => {
      db.get('SELECT fund_code FROM funds WHERE fund_code = ?', [fund_code], (err, row) => {
        if (err) reject(err); else resolve(row);
      });
    });
    if (!fund) {
      const urow = await new Promise((resolve, reject) => {
        db.get('SELECT fund_code, fund_name, fund_type FROM fund_universe WHERE fund_code = ?', [fund_code], (err, row) => {
          if (err) reject(err); else resolve(row);
        });
      });
      if (!urow) return res.status(404).json({ error: `基金 ${fund_code} 不在全市场基金库中` });
      // 入库 + 拉全量历史净值（观察池/信号/交易都依赖）
      const navN = await ensureFundWithNav({ fund_code: urow.fund_code, fund_name: urow.fund_name, fund_type: urow.fund_type });
      if (navN < 30) console.warn(`[手动观察] ${fund_code} 净值仅 ${navN} 条，信号可能不完整`);
    }

    await new Promise((resolve, reject) => {"""
assert c.count(old) == 1, 'manual watch count %d' % c.count(old)
c = c.replace(old, new, 1)

io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
