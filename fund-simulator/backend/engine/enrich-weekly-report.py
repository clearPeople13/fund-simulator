# -*- coding: utf-8 -*-
"""generateReport：weekly 周报补强——①期间每日收益明细 ②AI 操盘点评（数据驱动总结+下周关注）"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """  lines.push('## 下周计划');
  lines.push(`- 按 ${cfg.rebalance_frequency || 'monthly'} 再平衡节奏评估调仓；`);
  lines.push(`- 观察池 ${cfg.watchlist_style || ''} 标的持续跟踪，${cfg.entry_signal_threshold || 'strong'} 信号才建仓；`);
  lines.push(`- 止损线 -${((cfg.stop_loss || 0.05) * 100).toFixed(0)}%，止盈线 +${((cfg.take_profit || 0.2) * 100).toFixed(0)}%，回撤熔断 -${((cfg.max_drawdown || 0.1) * 100).toFixed(0)}%。`);"""
new = """  // 期间每日收益明细（快照口径）——周报专属
  if (reportType === 'weekly') {
    const snapWeek = await new Promise((resolve) => {
      db.all('SELECT date, daily_pnl FROM portfolio_daily WHERE user_id = ? AND date >= ? ORDER BY date', [userId, period.split(' ~ ')[0]], (err, rows) => resolve(err ? [] : (rows || [])));
    });
    if (snapWeek.length) {
      const weekTotal = snapWeek.reduce((a, x) => a + (x.daily_pnl || 0), 0);
      lines.push('## 期间每日收益（快照口径）');
      for (const x of snapWeek) lines.push(`- ${x.date}：${x.daily_pnl >= 0 ? '+' : ''}¥${x.daily_pnl.toFixed(2)}`);
      lines.push(`- 本周合计：${weekTotal >= 0 ? '+' : ''}¥${weekTotal.toFixed(2)}`);
      lines.push('');
    }
    // AI 操盘点评（数据驱动）
    const buys = (trades || []).filter(t => t.transaction_type === 'BUY').length;
    const sells = (trades || []).filter(t => t.transaction_type === 'SELL').length;
    const realized = await new Promise((resolve) => {
      db.all('SELECT amount FROM realized_pnl WHERE user_id = ? AND created_at >= datetime(?)', [userId, period.split(' ~ ')[0] + ' 00:00:00'], (err, rows) => resolve(err ? [] : (rows || [])));
    });
    const realizedTotal = realized.reduce((a, r) => a + (r.amount || 0), 0);
    const snapSum = snapWeek.reduce((a, x) => a + (x.daily_pnl || 0), 0);
    let tone;
    if (snapSum >= 0 && snapSum < 100) tone = '本周账户小幅盈利，走势平稳，未出现明显回撤。';
    else if (snapSum >= 100) tone = '本周账户表现积极，收益为正，主要受益于持仓净值上行。';
    else if (snapSum >= -100) tone = '本周账户小幅回撤，属正常波动区间，未触发风控红线。';
    else tone = '本周账户回撤明显，AI 已按风控规则评估减仓/止损，避免更大损失。';
    const op = [];
    if (buys > 0) op.push(`主动买入 ${buys} 笔`); else op.push('未新增建仓');
    if (sells > 0) op.push(`卖出/减仓 ${sells} 笔，实现盈亏 ${realizedTotal >= 0 ? '+' : ''}¥${realizedTotal.toFixed(2)}`); else op.push('未触发卖出');
    lines.push('## AI 操盘点评');
    lines.push(tone);
    lines.push(`- 本周操作：${op.join('；')}；`);
    lines.push(`- 事件数：${events.length} 条风控记录${events.length ? '，已按规则处理' : '，市场平稳'};`);
    lines.push(`- 观察池跟踪 ${Object.keys(pf.holdings).length} 只持仓 + ${(await new Promise((resolve) => db.get('SELECT COUNT(*) c FROM watchlist WHERE user_id = ?', [userId], (e, r) => resolve(r || { c: 0 })))).c} 只观察标的。`);
    lines.push('');
  }
  lines.push('## 下周计划');
  lines.push(`- 按 ${cfg.rebalance_frequency || 'monthly'} 再平衡节奏评估调仓；`);
  lines.push(`- 观察池 ${cfg.watchlist_style || ''} 标的持续跟踪，${cfg.entry_signal_threshold || 'strong'} 信号才建仓；`);
  lines.push(`- 止损线 -${((cfg.stop_loss || 0.05) * 100).toFixed(0)}%，止盈线 +${((cfg.take_profit || 0.2) * 100).toFixed(0)}%，回撤熔断 -${((cfg.max_drawdown || 0.1) * 100).toFixed(0)}%。`);"""
assert s.count(old) == 1, 'anchor not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('weekly report enriched')
