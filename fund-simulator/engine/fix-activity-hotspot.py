# -*- coding: utf-8 -*-
"""activity 轨迹支持 hotspot 记录：查 analysis_type/signal_label/signal_reason，热点行显示为“热点分析 主题 → 状态 + 点评”"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """    const anas = await all('SELECT fund_code, decision, confidence, entry_price, target_price, stop_loss, analysis_time FROM analysis_logs WHERE user_id = ? ORDER BY analysis_time DESC LIMIT 4', [userId]);"""
new = """    const anas = await all("SELECT analysis_type, fund_code, decision, confidence, entry_price, target_price, stop_loss, analysis_time, signal_label, signal_reason FROM analysis_logs WHERE user_id = ? ORDER BY analysis_time DESC LIMIT 5", [userId]);"""
assert s.count(old) == 1, 'sql not found'
s = s.replace(old, new)

old2 = """      items.push({ time: a.analysis_time, type: 'analysis', title: `分析 ${a.fund_code} → ${a.decision}${a.confidence ? '（' + a.confidence + '）' : ''}`, desc: `参考价 ¥${(a.entry_price || 0).toFixed(4)} · 目标 ¥${(a.target_price || 0).toFixed(4)} · 止损 ¥${(a.stop_loss || 0).toFixed(4)}` });"""
new2 = """      if (a.analysis_type === 'hotspot') {
        items.push({ time: a.analysis_time, type: 'hotspot', title: `热点分析 ${a.signal_label || '市场'} → ${a.decision}`, desc: a.signal_reason || '' });
      } else {
        items.push({ time: a.analysis_time, type: 'analysis', title: `分析 ${a.fund_code} → ${a.decision}${a.confidence ? '（' + a.confidence + '）' : ''}`, desc: `参考价 ¥${(a.entry_price || 0).toFixed(4)} · 目标 ¥${(a.target_price || 0).toFixed(4)} · 止损 ¥${(a.stop_loss || 0).toFixed(4)}` });
      }"""
assert s.count(old2) == 1, 'branch not found'
s = s.replace(old2, new2)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('activity hotspot branch patched')
