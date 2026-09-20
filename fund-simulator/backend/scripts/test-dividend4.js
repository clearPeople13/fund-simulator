const axios = require('axios');
const cheerio = require('cheerio');
(async () => {
  // 方案A：东财 F10DataApi 换 code + 常用 ut token
  for (const code of ['000001', '161725']) {
    try {
      const resp = await axios.get('https://api.fund.eastmoney.com/f10/F10DataApi', {
        params: { type: 'fhsp', code, page: 1, per: 5, ut: 'bd1d9ddb04089700cf9c27f6f7426281' },
        headers: { Referer: 'http://fundf10.eastmoney.com/', 'User-Agent': 'Mozilla/5.0' },
        timeout: 10000
      });
      const ls = resp.data && resp.data.Data && resp.data.Data.ls;
      console.log('A', code, '->', ls ? ls.join(' | ').slice(0, 200) : ('Data null / ' + JSON.stringify(resp.data).slice(0, 120)));
    } catch (e) { console.log('A', code, 'FAIL:', e.message); }
  }
  // 方案B：东财分红历史 HTML 页面
  try {
    const resp = await axios.get('https://fundf10.eastmoney.com/fhsp_005827.html', {
      headers: { 'User-Agent': 'Mozilla/5.0' }, timeout: 10000
    });
    const $ = cheerio.load(resp.data);
    const rows = $('.body .box tbody tr').length;
    const first = $('.body .box tbody tr').first().text().replace(/\s+/g, '|').slice(0, 120);
    console.log('B 005827 行数:', rows, '首行:', first);
  } catch (e) { console.log('B FAIL:', e.message); }
})();
