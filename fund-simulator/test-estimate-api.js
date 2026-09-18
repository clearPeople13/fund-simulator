const axios = require('axios');
(async () => {
  // 天天基金盘中估值接口（通常无需令牌）
  try {
    const resp = await axios.get('https://fundgz.1234567.com.cn/js/005827.js', {
      timeout: 8000, headers: { 'User-Agent': 'Mozilla/5.0', Referer: 'https://fund.eastmoney.com/' }
    });
    console.log('005827 估值原始:', String(resp.data).slice(0, 400));
  } catch (e) { console.log('005827 FAIL:', e.message); }
  try {
    const resp = await axios.get('https://fundgz.1234567.com.cn/js/000001.js', {
      timeout: 8000, headers: { 'User-Agent': 'Mozilla/5.0', Referer: 'https://fund.eastmoney.com/' }
    });
    console.log('000001 估值原始:', String(resp.data).slice(0, 400));
  } catch (e) { console.log('000001 FAIL:', e.message); }
})();
