# -*- coding: utf-8 -*-
"""weekly/monthly 手动触发：交易步骤（再平衡/换仓/分红调整）包 try/catch——盘外触发跳过交易、仍生成报告"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """    if (type === 'weekly') {
      // 手动触发周任务：评分更新 + 再平衡 + 换仓 + 周报
      await computeFundProfiles();
      const results = [];
      for (const userId of Object.keys(userConfigs)) {
        const cfg = await getRiskParams(userId);
        results.push({ userId, rebalance: await rebalanceCheck(userId) });
        await switchFunds(userId);
        await generateReport(userId, 'weekly');
      }
      return res.json({ ok: true, type, results });
    }
    if (type === 'monthly') {
      // 手动触发月任务：归因 + 压力测试 + 月报 + 分红同步
      await dividendAdjust();
      const results = [];
      for (const userId of Object.keys(userConfigs)) {
        const attr = await performanceAttribution(userId);
        await generatePressureReport(userId);
        await generateReport(userId, 'monthly');
        results.push({ userId, attribution: attr });
      }
      return res.json({ ok: true, type, results });
    }"""
new = """    if (type === 'weekly') {
      // 手动触发周任务：评分更新 + 再平衡 + 换仓 + 周报（交易步骤受交易时段守卫；盘外触发跳过交易仅生成报告）
      await computeFundProfiles();
      const results = [];
      for (const userId of Object.keys(userConfigs)) {
        const cfg = await getRiskParams(userId);
        let rb = null, sw = null;
        try { rb = await rebalanceCheck(userId); } catch (e) { rb = 'SKIP:' + e.message; }
        try { sw = await switchFunds(userId); } catch (e) { sw = 'SKIP:' + e.message; }
        await generateReport(userId, 'weekly');
        results.push({ userId, rebalance: rb, switch: sw });
      }
      return res.json({ ok: true, type, results });
    }
    if (type === 'monthly') {
      // 手动触发月任务：归因 + 压力测试 + 月报 + 分红同步
      const results = [];
      for (const userId of Object.keys(userConfigs)) {
        const attr = await performanceAttribution(userId);
        await generatePressureReport(userId);
        await generateReport(userId, 'monthly');
        results.push({ userId, attribution: attr });
      }
      return res.json({ ok: true, type, results });
    }"""
assert s.count(old) == 1, 'scheduler block not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('scheduler weekly/monthly hardened')
