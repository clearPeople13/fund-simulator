# -*- coding: utf-8 -*-
"""generateReport 月报追加"业绩归因（简化 Brinson）"小节（设计文档 §4.7 归因→写入月报）"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

anchor = """  lines.push('## 风控事件');
  if (events.length === 0) lines.push('- 无');
  for (const ev of events) lines.push(`- [${ev.event_type}] ${ev.fund_code || ''} ${ev.detail}（${utcToLocalStr(ev.created_at)}）`);
  lines.push('');
"""
assert s.count(anchor) == 1, 'risk events block not found'

add = """  lines.push('## 风控事件');
  if (events.length === 0) lines.push('- 无');
  for (const ev of events) lines.push(`- [${ev.event_type}] ${ev.fund_code || ''} ${ev.detail}（${utcToLocalStr(ev.created_at)}）`);
  lines.push('');
  if (reportType === 'monthly') {
    // 业绩归因（简化 Brinson）：配置贡献 vs 选基贡献（设计文档 §4.7）
    try {
      const attr = await performanceAttribution(userId);
      lines.push('## 业绩归因（简化 Brinson）');
      lines.push(`- 配置贡献：${attr.allocation.toFixed(2)}%　选基贡献：${attr.selection.toFixed(2)}%　总超额：${attr.totalExcess.toFixed(2)}%`);
      lines.push('');
    } catch (e) {
      lines.push('## 业绩归因');
      lines.push(`- 计算失败：${e.message}`);
      lines.push('');
    }
  }
"""
s = s.replace(anchor, add)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('attribution section added to monthly report')
