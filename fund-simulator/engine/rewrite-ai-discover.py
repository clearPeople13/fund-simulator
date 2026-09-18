# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js'
c = io.open(p, encoding='utf-8').read()

old = """    let score = 0;
    let matched = false;
    if (risk === 'high') {
      // 激进型：高波动 + 成长弹性
      if (['股票型', '混合型-偏股', 'QDII-普通股票', 'QDII-混合偏股'].includes(fund.fund_type) || isThematic) matched = true;
      if (matched) {
        score = (vol != null ? vol * 3 : 5) + Math.max(change20, 0) * 0.8 + Math.abs(drawdown) * 0.4;
        if (isThematic) score += 3;
        if (fund.fund_type === '股票型') score += 2;
        if (fund.above_ma20) score += 1.5;
      }
    } else {
      // 稳健型：低波动 + 宽基分散（排除行业主题基金）
      if (!isThematic && ['指数型-股票', '混合型-灵活', 'QDII-普通股票', '混合型-偏股'].includes(fund.fund_type)) matched = true;
      if (matched) {
        score = (vol != null ? 10 - vol : 5) + Math.max(change20, 0) * 0.5 + (drawdown >= -8 ? 3 : 0);
        if (fund.fund_type === '指数型-股票') score += 3;
        if (fund.fund_type === 'QDII-普通股票') score += 1.5;
        if (fund.above_ma20) score += 1.5;
      }
    }
    if (!matched) continue;"""
new = """    // 性格专属匹配（类型池零交集，天然不重叠）：
    // 激进型 = 高弹性类型（股票型/混合型-偏股/QDII）∪ 任何行业主题基金（弹性归激进）
    // 稳健型 = 非主题的宽基/均衡（指数型-股票/混合型-灵活），绝对排除行业主题
    let score = 0;
    let matched = false;
    const HIGH_TYPES = ['股票型', '混合型-偏股', 'QDII-普通股票', 'QDII-混合偏股'];
    const MID_TYPES = ['指数型-股票', '混合型-灵活'];
    if (risk === 'high') {
      if (HIGH_TYPES.includes(fund.fund_type) || isThematic) matched = true;
      if (matched) {
        // 高波动×弹性 + 强动量/超跌反弹空间 + 主题溢价 + 股票型溢价
        const volScore = vol != null ? vol * 2.5 : 5;
        const momScore = change20 > 0 ? Math.min(change20, 15) * 1.2 : Math.abs(change20) * 0.3;
        const ddScore = drawdown >= -5 ? 1 : drawdown >= -15 ? 3 : Math.min(Math.abs(drawdown) * 0.4, 6);
        score = volScore + momScore + ddScore
          + (isThematic ? 3 : 0)
          + (fund.fund_type === '股票型' ? 2 : 0)
          + (fund.above_ma20 ? 1 : 0);
      }
    } else {
      if (MID_TYPES.includes(fund.fund_type) && !isThematic) matched = true;
      if (matched) {
        // 低波动优先 + 温和动量 + 回撤控制 + 宽基指数溢价
        const volScore = vol != null ? Math.max(0, 12 - vol) * 2 : 6;
        const trendScore = change20 > 0 ? Math.min(change20, 10) * 0.5 : change20 * 0.3;
        const ddScore = drawdown >= -5 ? 4 : drawdown >= -10 ? 1 : -4;
        score = volScore + trendScore + ddScore
          + (fund.fund_type === '指数型-股票' ? 3 : 0)
          + (fund.above_ma20 ? 2 : 0);
      }
    }
    if (!matched) continue;"""
assert c.count(old) == 1, 'anchor count=%d' % c.count(old)
c = c.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK 性格专属选基逻辑')
