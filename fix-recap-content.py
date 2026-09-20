import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\backend\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = '''    lines.push('## 明日关注');
    lines.push('- ' + (cfg.name || userId) + '（' + (cfg.style || '') + '）：止损线 -' + ((cfg.stop_loss || 0.05) * 100).toFixed(0) + '%，止盈线 +' + ((cfg.take_profit || 0.2) * 100).toFixed(0) + '%');
    lines.push('- 关注持仓退场信号与观察池入场信号，' + (cfg.watchlist_style || '') + ' 方向标的优先');'''
new = '''    lines.push('## 明日关注');
    lines.push('- ' + (cfg.name || userId) + '（' + (cfg.style || '') + '）：止损线 -' + ((cfg.stop_loss || 0.05) * 100).toFixed(0) + '%，止盈线 +' + ((cfg.take_profit || 0.2) * 100).toFixed(0) + '%');
    // 持仓基金表现
    const hs = pf.holdings || [];
    if (hs.length) {
      const topGain = hs.reduce((a, b) => (b.pnl_pct || 0) > (a.pnl_pct || 0) ? b : a);
      const topLoss = hs.reduce((a, b) => (b.pnl_pct || 0) < (a.pnl_pct || 0) ? b : a);
      lines.push('- 持仓表现：' + topGain.fund_name + ' +' + (topGain.pnl_pct || 0).toFixed(2) + '% 领涨，' + topLoss.fund_name + ' ' + (topLoss.pnl_pct || 0).toFixed(2) + '% 领跌');
    }
    // 热点方向
    if (hotspots && hotspots.themes && hotspots.themes.length) {
      const topTheme = hotspots.themes[0];
      lines.push('- 热点方向：' + topTheme.name + '（热度' + topTheme.score + '），' + (topTheme.avg_chg >= 0 ? '涨' : '跌') + (Math.abs(topTheme.avg_chg || 0)).toFixed(2) + '%');
    }
    lines.push('- 关注持仓退场信号与观察池入场信号，' + (cfg.watchlist_style || '') + ' 方向标的优先');'''
assert s.count(old) == 1
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('daily recap enriched')
