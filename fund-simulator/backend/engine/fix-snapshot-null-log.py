# -*- coding: utf-8 -*-
"""saveDailySnapshot 返回 null 时，启动/收盘分析调用点跳过打印，避免 null.date 报错"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old1 = """          const snapshot = await saveDailySnapshot(userId);
          console.log(`已保存 ${userConfigs[userId].name} 账户快照: ${snapshot.date} 总资产¥${snapshot.total.toFixed(2)} 当日盈亏¥${snapshot.dailyPnl.toFixed(2)}`);"""
new1 = """          const snapshot = await saveDailySnapshot(userId);
          if (snapshot) console.log(`已保存 ${userConfigs[userId].name} 账户快照: ${snapshot.date} 总资产¥${snapshot.total.toFixed(2)} 当日盈亏¥${snapshot.dailyPnl.toFixed(2)}`);"""
assert s.count(old1) == 1, 'block1 not found'
s = s.replace(old1, new1)

old2 = """        const snapshot = await saveDailySnapshot(userId);
        console.log(`已保存 ${userConfigs[userId].name} 启动快照: ${snapshot.date} 总资产¥${snapshot.total.toFixed(2)} 当日盈亏¥${snapshot.dailyPnl.toFixed(2)}`);"""
new2 = """        const snapshot = await saveDailySnapshot(userId);
        if (snapshot) console.log(`已保存 ${userConfigs[userId].name} 启动快照: ${snapshot.date} 总资产¥${snapshot.total.toFixed(2)} 当日盈亏¥${snapshot.dailyPnl.toFixed(2)}`);"""
assert s.count(old2) == 1, 'block2 not found'
s = s.replace(old2, new2)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('server.js patched')
