# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js'
c = io.open(p, encoding='utf-8').read()

# 1. require child_process
old = "const fs = require('fs');"
new = "const fs = require('fs');\nconst { spawn } = require('child_process');"
assert c.count(old) == 1, 'require %d' % c.count(old)
c = c.replace(old, new, 1)

# 2. 插入每日全市场基金库刷新调度（22:05）
anchor = "// 实时分析 - 每30分钟"
schedule = """// 全市场基金库每日刷新（rankhandler 快照，供 AI 全市场选基与基金库展示；子进程不阻塞主服务）
function scheduleUniverseSync() {
  const run = () => {
    console.log('[全市场基金库] 开始刷新 fund_universe ...');
    const child = spawn(process.execPath, [path.join(__dirname, 'engine', 'sync-fund-universe.js')], {
      stdio: ['ignore', 'pipe', 'pipe']
    });
    child.stdout.on('data', d => process.stdout.write('[universe] ' + String(d)));
    child.stderr.on('data', d => process.stderr.write('[universe-err] ' + String(d)));
    child.on('exit', code => console.log('[全市场基金库] 刷新结束 code=' + code));
  };
  const now = new Date();
  const target = new Date(now);
  target.setHours(22, 5, 0, 0);
  if (now > target) target.setDate(target.getDate() + 1);
  const delay = target.getTime() - now.getTime();
  setTimeout(() => {
    run();
    setInterval(run, 24 * 60 * 60 * 1000);
  }, delay);
  console.log('[全市场基金库] 每日 22:05 自动刷新（首次 ' + target.toLocaleString() + '）');
}

"""
assert c.count(anchor) == 1, 'anchor %d' % c.count(anchor)
c = c.replace(anchor, schedule + anchor, 1)

# 3. 启动时调用
old2 = "  // 启动定时任务\n  scheduleAnalysis();"
new2 = "  // 启动定时任务\n  scheduleAnalysis();\n  scheduleUniverseSync();"
assert c.count(old2) == 1, 'boot %d' % c.count(old2)
c = c.replace(old2, new2, 1)

io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
