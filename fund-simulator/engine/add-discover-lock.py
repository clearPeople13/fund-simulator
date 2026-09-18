# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js'
c = io.open(p, encoding='utf-8').read()

# 1. 原函数改名
old = "// AI 按用户性格从全市场自主选基并维护观察池（source='ai'，上限 KEEP 只；手动项永不删除；只影响观察池，不涉及交易）\n// 候选池 = 全市场基金库 fund_universe（天天基金排行快照，股票型/混合型/指数型/QDII 共 1.4万+ 只）\nasync function aiDiscoverWatchlist(userId) {"
new = "// AI 按用户性格从全市场自主选基并维护观察池（source='ai'，上限 KEEP 只；手动项永不删除；只影响观察池，不涉及交易）\n// 候选池 = 全市场基金库 fund_universe（天天基金排行快照，股票型/混合型/指数型/QDII 共 1.4万+ 只）\nasync function aiDiscoverWatchlistInner(userId) {"
assert c.count(old) == 1, 'rename count %d' % c.count(old)
c = c.replace(old, new, 1)

# 2. 在函数前插入带锁包装
anchor = "// AI 按用户性格从全市场自主选基并维护观察池"
lock_code = """// 观察池互斥锁：避免启动自动选基与用户手动触发/定时分析并发竞态（先删后插必须串行）
let discoverLock = null;
async function aiDiscoverWatchlist(userId) {
  while (discoverLock) await new Promise(r => setTimeout(r, 400));
  discoverLock = true;
  try {
    return await aiDiscoverWatchlistInner(userId);
  } finally {
    discoverLock = false;
  }
}

// AI 按用户性格从全市场自主选基并维护观察池"""
assert c.count(anchor) == 1, 'anchor count %d' % c.count(anchor)
c = c.replace(anchor, lock_code, 1)

io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
