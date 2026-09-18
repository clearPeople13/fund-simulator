# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js'
c = io.open(p, encoding='utf-8').read()

# ========== 性格匹配：收益弹性 + 类型 + 主题 ==========
old = """    let matched = false;
    let score = 0;
    if (risk === 'high') {
      // 激进：高弹性类型（股票型/QDII）∪ 任何行业主题基金；弹性 = 强动量 + 主题溢价 + 超跌反弹空间
      if (f.fund_type === '股票型' || f.fund_type === 'QDII' || theme) matched = true;
      if (matched) {
        score = Math.max(r1y, 0) * 0.5 + Math.max(r3m, 0) * 0.6 + Math.max(day, 0) * 1.2
          + (theme ? 3 : 0) + (f.fund_type === '股票型' ? 2 : 0)
          + (r6m < 0 ? Math.min(Math.abs(r6m) * 0.15, 5) : 0);
      }
    } else {
      // 稳健：非主题的宽基/均衡（指数型/混合型）；稳定 = 长期正收益 + 回撤控制 + 温和动量
      if ((f.fund_type === '指数型' || f.fund_type === '混合型') && !theme) matched = true;
      if (matched) {
        score = Math.max(r1y, 0) * 0.5 + Math.max(r6m, 0) * 0.3 + Math.max(day, 0) * 0.3
          + (r3m >= 0 ? 1.0 : 0) + (r6m < -15 ? -4 : 0) + (f.fund_type === '指数型' ? 6 : 0);
      }
    }"""
new = """    let matched = false;
    let score = 0;
    if (risk === 'high') {
      // 激进：高弹性（近1年 >40%）∪ 高弹性类型（股票型/QDII）∪ 任何行业主题基金
      // 弹性 = 强动量 + 主题溢价 + 超跌反弹空间
      if (f.fund_type === '股票型' || f.fund_type === 'QDII' || theme || r1y > 40) matched = true;
      if (matched) {
        score = Math.max(r1y, 0) * 0.5 + Math.max(r3m, 0) * 0.6 + Math.max(day, 0) * 1.2
          + (theme ? 3 : 0) + (f.fund_type === '股票型' ? 2 : 0)
          + (r6m < 0 ? Math.min(Math.abs(r6m) * 0.15, 5) : 0);
      }
    } else {
      // 稳健：宽基指数（指数型）∪ 收益温和的均衡混合（近1年 <40% 且非主题）；稳定 = 长期正收益 + 回撤控制
      if ((f.fund_type === '指数型' || (f.fund_type === '混合型' && !theme && r1y < 40))) matched = true;
      if (matched) {
        score = Math.max(r1y, 0) * 0.5 + Math.max(r6m, 0) * 0.3 + Math.max(day, 0) * 0.3
          + (r3m >= 0 ? 1.0 : 0) + (r6m < -15 ? -4 : 0) + (f.fund_type === '指数型' ? 6 : 0);
      }
    }"""
assert c.count(old) == 1, 'match count %d' % c.count(old)
c = c.replace(old, new, 1)

io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
