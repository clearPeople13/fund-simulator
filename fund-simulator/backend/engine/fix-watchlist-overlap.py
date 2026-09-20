# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js'
c = io.open(p, encoding='utf-8').read()

old = """  const manualSet = new Set(existing.filter(x => x.source !== 'ai').map(x => x.fund_code));
  const aiSet = new Set(existing.filter(x => x.source === 'ai').map(x => x.fund_code));

  const candidates = [];
  for (const fund of pool) {
    if (fund.latest_nav == null || fund.latest_nav <= 0) continue;
    if (manualSet.has(fund.fund_code)) continue;
"""
new = """  const manualSet = new Set(existing.filter(x => x.source !== 'ai').map(x => x.fund_code));
  const aiSet = new Set(existing.filter(x => x.source === 'ai').map(x => x.fund_code));

  // 跨用户去重：其他用户的观察池（全部来源）与持仓，本用户 AI 不再重复关注（性格分工）
  const otherWatchSet = await new Promise((resolve) => {
    db.all('SELECT DISTINCT fund_code FROM watchlist WHERE user_id != ?', [userId], (err, rows) => {
      resolve(err ? new Set() : new Set((rows || []).map(r => r.fund_code)));
    });
  });
  const otherHoldSet = await new Promise((resolve) => {
    db.all('SELECT DISTINCT fund_code FROM holdings WHERE user_id != ? AND shares > 0', [userId], (err, rows) => {
      resolve(err ? new Set() : new Set((rows || []).map(r => r.fund_code)));
    });
  });

  const candidates = [];
  for (const fund of pool) {
    if (fund.latest_nav == null || fund.latest_nav <= 0) continue;
    if (manualSet.has(fund.fund_code)) continue;
    if (otherWatchSet.has(fund.fund_code)) continue; // 其他用户已观察
    if (otherHoldSet.has(fund.fund_code)) continue;  // 其他用户已持仓
"""
assert c.count(old) == 1, 'anchor count=%d' % c.count(old)
c = c.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK server.js 跨用户去重')
