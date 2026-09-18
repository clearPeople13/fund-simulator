# -*- coding: utf-8 -*-
"""费用统计：/api/ai/portfolio 加 fee_stats；Analysis.vue 加累计费用卡+明细；月报加费用小节"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) /api/ai/portfolio 加 fee_stats
old = """    // 今日盈亏：取 portfolio_daily 最新快照（收盘按真实净值计算）
    const todayPnlRow = await new Promise((resolve) => {
      db.get('SELECT daily_pnl FROM portfolio_daily WHERE user_id = ? ORDER BY date DESC LIMIT 1', [userId], (err, row) => resolve(err ? null : row));
    });"""
new = """    // 今日盈亏：取 portfolio_daily 最新快照（收盘按真实净值计算）
    const todayPnlRow = await new Promise((resolve) => {
      db.get('SELECT daily_pnl FROM portfolio_daily WHERE user_id = ? ORDER BY date DESC LIMIT 1', [userId], (err, row) => resolve(err ? null : row));
    });
    // 费用统计：申购费（BUY）/赎回费（SELL）按交易记录汇总（口径=各交易 fees 字段）
    const feeStats = await new Promise((resolve) => {
      db.all('SELECT transaction_type, SUM(fees) AS fee FROM transactions WHERE user_id = ? GROUP BY transaction_type', [userId], (err, rows) => {
        if (err) return resolve({ buy_fee: 0, sell_fee: 0, total_fee: 0 });
        let buy = 0, sell = 0;
        (rows || []).forEach(r => { if (r.transaction_type === 'BUY') buy += r.fee || 0; else if (r.transaction_type === 'SELL') sell += r.fee || 0; });
        const round2 = v => Math.round(v * 100) / 100;
        resolve({ buy_fee: round2(buy), sell_fee: round2(sell), total_fee: round2(buy + sell) });
      });
    });"""
assert s.count(old) == 1, 'todayPnl block not found'
s = s.replace(old, new)

old2 = """      total_assets: portfolio.current_capital + marketValueTotal,
      today_pnl: todayPnlRow ? todayPnlRow.daily_pnl : 0
    });"""
new2 = """      total_assets: portfolio.current_capital + marketValueTotal,
      today_pnl: todayPnlRow ? todayPnlRow.daily_pnl : 0,
      fee_stats: feeStats
    });"""
assert s.count(old2) == 1, 'res.json block not found'
s = s.replace(old2, new2)

# 2) 月报加费用小节（在业绩归因小节后）
old3 = """      lines.push('## 业绩归因');
      lines.push(`- 计算失败：${e.message}`);
      lines.push('');
    }
  }
  lines.push('## 下周计划');"""
new3 = """      lines.push('## 业绩归因');
      lines.push(`- 计算失败：${e.message}`);
      lines.push('');
    }
    // 费用统计：期间交易费用（与交易流水可对账）+ 累计费用
    let periodBuy = 0, periodSell = 0;
    (trades || []).forEach(t => { if (t.transaction_type === 'BUY') periodBuy += t.fees || 0; else if (t.transaction_type === 'SELL') periodSell += t.fees || 0; });
    const feeAll = await new Promise((resolve) => {
      db.all('SELECT transaction_type, SUM(fees) AS fee FROM transactions WHERE user_id = ? GROUP BY transaction_type', [userId], (err, rows) => {
        let b = 0, g = 0; (rows || []).forEach(r => { if (r.transaction_type === 'BUY') b += r.fee || 0; else if (r.transaction_type === 'SELL') g += r.fee || 0; });
        resolve({ b, g });
      });
    });
    lines.push('## 费用统计');
    lines.push(`- 期间交易费用：申购费 ¥${periodBuy.toFixed(2)}　赎回费 ¥${periodSell.toFixed(2)}（合计 ¥${(periodBuy + periodSell).toFixed(2)}）`);
    lines.push(`- 累计费用：申购费 ¥${feeAll.b.toFixed(2)}　赎回费 ¥${feeAll.g.toFixed(2)}（合计 ¥${(feeAll.b + feeAll.g).toFixed(2)}）`);
    lines.push('');
  }
  lines.push('## 下周计划');"""
assert s.count(old3) == 1, 'monthly report block not found'
s = s.replace(old3, new3)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('server.js patched')

# 3) Analysis.vue
p = os.path.join(BASE, 'frontend', 'src', 'views', 'Analysis.vue')
with io.open(p, 'r', encoding='utf-8') as f:
    v = f.read()

# 3.1 顶部 stats-grid 加累计费用卡（收益率卡后）
oldv1 = """      <div class="stat-card" :class="portfolioStats.totalReturnRate >= 0 ? 'stat-green' : 'stat-red'">
        <div class="stat-icon"><DashboardOutlined /></div>
        <div class="stat-body">
          <div class="stat-label">收益率</div>
          <div class="stat-value">{{ portfolioStats.totalReturnRate >= 0 ? '+' : '' }}{{ portfolioStats.totalReturnRate }}%</div>
        </div>
      </div>
    </div>"""
newv1 = """      <div class="stat-card" :class="portfolioStats.totalReturnRate >= 0 ? 'stat-green' : 'stat-red'">
        <div class="stat-icon"><DashboardOutlined /></div>
        <div class="stat-body">
          <div class="stat-label">收益率</div>
          <div class="stat-value">{{ portfolioStats.totalReturnRate >= 0 ? '+' : '' }}{{ portfolioStats.totalReturnRate }}%</div>
        </div>
      </div>
      <div class="stat-card stat-gold">
        <div class="stat-icon"><TagsOutlined /></div>
        <div class="stat-body">
          <div class="stat-label">累计费用</div>
          <div class="stat-value">¥{{ feeStats.total_fee.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</div>
        </div>
      </div>
    </div>"""
assert v.count(oldv1) == 1, 'stats-grid not found'
v = v.replace(oldv1, newv1)

# 3.2 收益指标加费用明细（Beta 后）
oldv2 = """              <div class="metric-item">
                <span class="label">系统风险 Beta</span>
                <span class="value muted">— 数据不足</span>
              </div>"""
newv2 = """              <div class="metric-item">
                <span class="label">系统风险 Beta</span>
                <span class="value muted">— 数据不足</span>
              </div>
              <div class="metric-item">
                <span class="label">累计费用（含买卖手续费）</span>
                <span class="value">¥{{ feeStats.total_fee.toFixed(2) }}</span>
              </div>
              <div class="metric-item">
                <span class="label">· 申购费 / 赎回费</span>
                <span class="value muted">¥{{ feeStats.buy_fee.toFixed(2) }} / ¥{{ feeStats.sell_fee.toFixed(2) }}</span>
              </div>"""
assert v.count(oldv2) == 1, 'metrics-card not found'
v = v.replace(oldv2, newv2)

# 3.3 data 加 feeStats + loadData 填充
oldv3 = """    portfolioStats.value = {
      initial_capital: initial,
      current_assets: currentAssets,
      totalReturn,
      totalReturnRate,
      tradingCount: txs.length
    }"""
newv3 = """    portfolioStats.value = {
      initial_capital: initial,
      current_assets: currentAssets,
      totalReturn,
      totalReturnRate,
      tradingCount: txs.length
    }
    feeStats.value = {
      buy_fee: Number(pf.fee_stats?.buy_fee || 0),
      sell_fee: Number(pf.fee_stats?.sell_fee || 0),
      total_fee: Number(pf.fee_stats?.total_fee || 0)
    }"""
assert v.count(oldv3) == 1, 'portfolioStats assign not found'
v = v.replace(oldv3, newv3)

# 3.4 声明 feeStats ref（在 portfolioStats ref 附近；先找 portfolioStats 定义）
import re
m = re.search(r'const portfolioStats = ref\([^)]*\)', v)
assert m, 'portfolioStats ref not found'
oldv4 = m.group(0)
newv4 = oldv4 + "\nconst feeStats = ref({ buy_fee: 0, sell_fee: 0, total_fee: 0 })"
v = v.replace(oldv4, newv4, 1)

# 3.5 引入 TagsOutlined（在现有图标 import 处追加）
oldv5 = "import { ThunderboltOutlined, LineChartOutlined, DollarOutlined, DashboardOutlined, WalletOutlined } from '@ant-design/icons-vue'"
if v.count(oldv5) == 0:
    # 找任意 @ant-design/icons-vue import 行
    m5 = re.search(r"import \{([^}]*)\} from '@ant-design/icons-vue'", v)
    assert m5, 'icons import not found'
    oldv5 = m5.group(0)
    newv5 = oldv5.replace('}', ', TagsOutlined }')
    v = v.replace(oldv5, newv5, 1)
else:
    v = v.replace(oldv5, oldv5.replace('}', ', TagsOutlined }'), 1)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(v)
print('Analysis.vue patched')
