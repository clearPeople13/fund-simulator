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
 * AI 基金经理分析单只基金
 * @param {object} fund - 基金数据（名称/代码/净值/涨跌/技术指标）
 * @param {string} userStyle - 用户风格（稳健型/激进型）
 * @returns {Promise<object>} { decision: 'BUY'|'HOLD'|'SELL', reason: '...' }
 */
async function analyzeFund(fund, userStyle) {
  const systemPrompt = `你是一位专业的基金经理，负责管理${userStyle}风格的基金组合。
你的任务：根据提供的基金数据，判断应该买入、持有还是卖出。
请严格按以下 JSON 格式回复：
{
  "decision": "BUY" 或 "HOLD" 或 "SELL",
  "confidence": "高" 或 "中" 或 "低",
  "reason": "简短分析理由（50字以内）"
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

module.exports = { callMIMO, analyzeFund };
