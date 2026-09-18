const axios = require('axios');
(async () => {
  try {
    const resp = await axios.get('https://api.fund.eastmoney.com/f10/F10DataApi', {
      params: { type: 'fhsp', code: '005827', page: 1, per: 5 },
      headers: { Referer: 'http://fundf10.eastmoney.com/', 'User-Agent': 'Mozilla/5.0' },
      timeout: 10000
    });
    console.log('Data:', JSON.stringify(resp.data.Data).slice(0, 600));
  } catch (e) {
    console.error('FAIL:', e.message);
  }
})();
