const axios = require('axios');
(async () => {
  try {
    const resp = await axios.get('https://hq.sinajs.cn/list=sh510300', {
      headers: { 'Referer': 'https://finance.sina.com.cn/', 'User-Agent': 'Mozilla/5.0' },
      timeout: 8000,
      responseType: 'arraybuffer'
    });
    const text = new TextDecoder('gbk').decode(Buffer.from(resp.data));
    console.log('LEN', text.length);
    console.log(text.slice(0, 200));
    const m = text.match(/="([^"]*)"/);
    console.log('MATCH:', !!m);
    if (m) {
      const f = m[1].split(',');
      console.log('FIELDS', f.length, 'price', f[3], 'prev', f[2], 'date', f[30], 'time', f[31]);
    }
  } catch (e) {
    console.log('ERR', e.message);
  }
})();
