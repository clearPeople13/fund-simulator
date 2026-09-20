# -*- coding: utf-8 -*-
"""SYSTEM_KNOWLEDGE.md §9 项3-6 状态更新 + 修复史追加归因修复"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\SYSTEM_KNOWLEDGE.md"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 项 3：定投保持可选（标注评估结论）
old3 = u"3. 定投 / 定期计划（规格 §4.3）未实施。"
new3 = u"3. ~~定投 / 定期计划（规格 §4.3）~~ **评估结论（2026-09-18）：不实施**——设计文档本就标\"⬜ 可选\"；AI 的定期小额加仓语义已由\"分批加仓 + 冷却期（5/3 天）\"覆盖，且系统铁律是 AI 自主决策（用户设定的机械定投与此冲突），另开一条买入路径反而增加\"乱买\"风险。"
assert s.count(old3) == 1, 'item3 not found'
s = s.replace(old3, new3)

# 项 4：完成
old4 = u"4. 分红 / 归因 / 压力测试依赖月 / 月初自动触发（手动触发 API 可验证）。"
new4 = u"4. ~~分红 / 归因 / 压力测试月度触发待验证~~ **已完成（2026-09-18）**：链路本就实现（分红每月 1-3 日自动同步、归因/压力/月报月末最后交易日自动触发），手动 POST /api/scheduler/run type=monthly 实测全通（default 归因 配置 0.40%/选基 -1.19%/总超额 -0.80%；aggressive 0.45%/-1.27%/-0.82%，压力报告+月报落库）；**修复缺口：归因结果此前只回 API 不写月报正文，现月报追加\"业绩归因（简化 Brinson）\"小节**。"
assert s.count(old4) == 1, 'item4 not found'
s = s.replace(old4, new4)

# 项 5：完成（验收）
old5 = u"5. 未跟踪基金（tracked=false）详情页 \"点 ☆ 观察 自动拉净值\" 待用户最终验收。"
new5 = u"5. ~~未跟踪基金 ☆ 观察待验收~~ **已完成（2026-09-18，浏览器实测通过）**：基金库 012414 ☆ 观察 → POST 自动入库（universe 兜底）+ 拉全量净值（1300 条）→ ★ 已观察 → 详情页完整渲染 → AI 信号\"暂缓入场\"（近20日 -5%、20日线下方），全程只读不交易；验收数据已回滚（watchlist 恢复 56、funds 删除、净值保留）。备注：bu.click 对 AntD 按钮偶发不触发，需 JS dispatch click。"
assert s.count(old5) == 1, 'item5 not found'
s = s.replace(old5, new5)

# 项 6：完成（排程确认，首次自动执行待明日日志）
old6 = u"6. fund\\_universe 每日 22:05 自动刷新已接入，尚未实际等到自动运行验证（手动已跑通）。"
new6 = u"6. ~~fund\\_universe 每日 22:05 自动刷新待验证~~ **已完成（2026-09-18）**：启动日志确认排程生效（\"每日 22:05 自动刷新，首次 2026/9/18 22:05\"）；首次自动执行发生在今晚 22:05，次日查日志（[全市场基金库] 开始刷新…code=0）即可确认。"
assert s.count(old6) == 1, 'item6 not found'
s = s.replace(old6, new6)

# 修复史：追加归因缺口修复
oldfix = u"| 09-18 | funds 表被 AI 扫描喂大（101 只，大量淘汰孤儿） | 清理 42 只无引用基金（funds→59），净值历史保留；基金库=universe 不受影响；定期重跑 cleanup-funds-orphans.js |"
newfix = oldfix + u"\n| 09-18 | 归因结果不写入月报正文（仅 API 返回） | generateReport 月报追加\"业绩归因（简化 Brinson）\"小节（配置/选基/总超额） |"
assert s.count(oldfix) == 1, 'fix line not found'
s = s.replace(oldfix, newfix)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('knowledge base items 3-6 updated')
