// AI 分析模块：调用 MIMO Pro 2.5 大模型生成基金分析
const MIMO_API_KEY = 'tp-cg83vouwhbmrd8f6gcwtpobz7xb5ws6nf0c4t9mawcediyyq';
const MIMO_BASE_URL = 'https://token-plan-cn.xiaomimimo.com/v1';
const MIMO_MODEL = 'mimo-v2.5-pro';

/**
 * 调用 MIMO 大模型生成分析
 * @param {string} systemPrompt - 系统提示词（基金经理角色）
 * @param {string} userPrompt - 用户问题（基金数据+市场情况）
 * @returns {Promise<string>} AI 回复
 */
async function callMIMO(systemPrompt, userPrompt) {
  try {
    const body = {
      model: MIMO_MODEL,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt }
      ],
      temperature: 0.7,
      max_tokens: 2000
    };
    const res = await fetch(MIMO_BASE_URL + '/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + MIMO_API_KEY
      },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (data.choices && data.choices[0]) {
      return data.choices[0].message.content;
    }
    console.error('[AI] MIMO 返回异常: ' + JSON.stringify(data));
    return null;
  } catch (e) {
    console.error('[AI] MIMO 调用失败: ' + e.message);
    return null;
  }
}

/**
 * 获取用户性格画像（详细版，传给 AI 让它真正理解这个基金经理的风格）
 */
function getPersonalityProfile(style) {
  if (style === '激进型' || style === 'aggressive') {
    return {
      role: '一位激进型基金经理，追求高收益，愿意承担较大回撤',
      risk: '风险承受能力高，能接受短期15-20%的回撤',
      entry: '入场门槛低，只要技术面有向好迹象就敢买入，喜欢左侧布局',
      position: '单基金仓位最高可到40%，总仓位最高可达100%（满仓）',
      stop: '止损线较宽（-10%），给行情足够的波动空间',
      takeProfit: '止盈线高（+40%），不轻易止盈，让利润奔跑',
      style: '选股偏好成长型、主题型、高弹性基金，喜欢追热点和板块轮动',
      action: '操作积极，回调企稳就加仓，节奏快（加仓冷却期仅3天）',
      discipline: '纪律相对灵活，只要逻辑没变就持有，不因短期波动轻易离场'
    };
  }
  // 默认稳健型
  return {
    role: '一位稳健型基金经理，追求长期稳定收益，控制回撤是第一要务',
    risk: '风险承受能力中等，最大回撤控制在10%以内',
    entry: '入场门槛高，需要技术面+基本面共振才买入，不轻易追高',
    position: '单基金仓位上限20%，总仓位上限60%，永远不满仓',
    stop: '止损线严格（-5%），触及即走，不抱侥幸',
    takeProfit: '止盈线适中（+20%），分批止盈，落袋为安',
    style: '选股偏好大盘蓝筹、均衡配置型基金，不追热点，注重基金经理和长期业绩',
    action: '操作谨慎，分批建仓（首笔20%），加仓节奏慢（冷却期5天）',
    discipline: '纪律性强，严格执行止损止盈，不情绪化操作'
  };
}

/**
 * AI 基金经理分析单只基金
 * @param {object} fund - 基金数据（名称/代码/净值/涨跌/技术指标）
 * @param {string} userStyle - 用户风格（稳健型/激进型）
 * @returns {Promise<object>} { decision: 'BUY'|'HOLD'|'SELL', reason: '...' }
 */
async function analyzeFund(fund, userStyle) {
  const personality = getPersonalityProfile(userStyle);
  const systemPrompt = `你是${personality.role}。

你的投资性格：
- 风险偏好：${personality.risk}
- 入场策略：${personality.entry}
- 仓位控制：${personality.position}
- 止损纪律：${personality.stop}
- 止盈策略：${personality.takeProfit}
- 选股风格：${personality.style}
- 操作节奏：${personality.action}
- 纪律性：${personality.discipline}

你的任务：根据提供的基金数据，严格按照你的投资性格判断应该买入、持有还是卖出。
请严格按以下 JSON 格式回复：
{
  "decision": "BUY" 或 "HOLD" 或 "SELL",
  "confidence": "高" 或 "中" 或 "低",
  "reason": "简短分析理由（50字以内，体现你的性格判断逻辑）"
}`;

  const userPrompt = `基金信息：
- 名称：${fund.fund_name}（${fund.fund_code}）
- 最新净值：${fund.latest_nav}
- 今日涨跌：${fund.daily_return}%
- 近5日涨跌：${fund.change_5d}%
- 近20日涨跌：${fund.change_20d}%
- 近60日最大回撤：${fund.drawdown_60d}%
- 是否站上MA20：${fund.above_ma20 ? '是' : '否'}

请判断应该买入、持有还是卖出？`;

  const result = await callMIMO(systemPrompt, userPrompt);
  if (!result) return { decision: 'HOLD', confidence: '低', reason: 'AI 分析失败，默认持有' };

  try {
    // 提取 JSON
    const jsonMatch = result.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      return {
        decision: parsed.decision || 'HOLD',
        confidence: parsed.confidence || '低',
        reason: parsed.reason || 'AI 分析完成'
      };
    }
  } catch (e) {
    console.error('[AI] 解析失败: ' + e.message);
  }

  return { decision: 'HOLD', confidence: '低', reason: result.substring(0, 50) };
}

module.exports = { callMIMO, analyzeFund, getPersonalityProfile };
