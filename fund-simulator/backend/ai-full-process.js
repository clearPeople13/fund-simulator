// AI 全流程分析：全市场扫描 → 观察池更新 → 持仓分析 → 风控 → 复盘
const { callMIMO } = require('./ai-advisor');

async function fullAIProcess(userId) {
  console.log(`[AI全流程] ${userId} 开始...`);
  
  // 1. 全市场扫描 + 观察池更新
  console.log('[AI全流程] 1/5 全市场扫描 + 观察池更新...');
  const { aiDiscoverWatchlist } = require('./server'); // 这个不对，应该用路由传过来的
  
  // 2. 持仓分析
  console.log('[AI全流程] 2/5 持仓分析...');
  
  // 3. 买入/卖出决策
  console.log('[AI全流程] 3/5 买入/卖出决策...');
  
  // 4. 风控检查
  console.log('[AI全流程] 4/5 风控检查...');
  
  // 5. 生成复盘报告
  console.log('[AI全流程] 5/5 生成复盘报告...');
  
  console.log(`[AI全流程] ${userId} 完成`);
}

module.exports = { fullAIProcess };
