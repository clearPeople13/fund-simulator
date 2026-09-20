// 飞书通知模块：AI 买入/卖出/预警/复盘完成 → 推送飞书群
const FEISHU_WEBHOOK = 'https://open.feishu.cn/open-apis/bot/v2/hook/488d7ca1-b75a-41ca-92ff-0d2a2ea11aa7';

// 根据标题判断类型，加 emoji 和颜色
function getEmoji(title) {
  if (title.includes('买入')) return '\U0001F7E2'; // 🟢
  if (title.includes('卖出')) return '\U0001F534'; // 🔴
  if (title.includes('预警') || title.includes('风控')) return '\u26A0\uFE0F'; // ⚠️
  if (title.includes('复盘')) return '\U0001F4CA'; // 📊
  if (title.includes('分析')) return '\U0001F916'; // 🤖
  if (title.includes('观察池')) return '\U0001F50D'; // 🔍
  if (title.includes('订单确认')) return '\u2705'; // ✅
  return '\U0001F4E2'; // 📢
}

async function sendFeishu(title, content) {
  try {
    const emoji = getEmoji(title);
    const now = new Date().toLocaleString('zh-CN');
    const lines = content.split('\n');
    const postContent = lines.map(line => [{ tag: 'text', text: line }]);
    const body = {
      msg_type: 'post',
      content: {
        post: {
          zh_cn: {
            title: emoji + ' ' + title,
            content: postContent
          }
        }
      }
    };
    const res = await fetch(FEISHU_WEBHOOK, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (data.code === 0) console.log('[飞书] 推送成功: ' + title);
    else console.error('[飞书] 推送失败: ' + JSON.stringify(data));
  } catch (e) {
    console.error('[飞书] 推送异常: ' + e.message);
  }
}

module.exports = { sendFeishu };
