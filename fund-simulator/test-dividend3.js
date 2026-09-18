const axios = require('axios');
(async () => {
  for (const url of [
    'https://api.fund.eastmoney.com/f10/F10DataApi?type=fhsp&code=005827&page=1&per=5',
    'https://api.fund.eastmoney.com/f10/F10DataApi?type=fhsp&code=005827&page=1&per=5&callback=jsonp1'
  ]) {
    try {
      const resp = await axios.get(url, {
        headers: { Referer: 'http://fundf10.eastmoney.com/', 'User-Agent': 'Mozilla/5.0' },
        timeout: 10000
      });
      const d = typeof resp.data === 'string' ? resp.data.slice(0, 300) : JSON.stringify(resp.data).slice(0, 300);
      console.log('---', url.slice(0, 60));
      console.log(d);
    } catch (e) {
      console.log('FAIL:', e.message);
    }
  }
})();
