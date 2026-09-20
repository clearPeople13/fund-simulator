# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\data-fetcher.js'
c = io.open(p, encoding='utf-8').read()

old_head = """    /**
     * 获取基金实时估值（使用正确的API）
     * @param {string} fundCode 基金代码
     * @returns {Promise<Object>} 实时估值数据
     */
    async getRealTimeEstimate(fundCode) {
        try {
            // 使用东方财富的基金估值API
            const url = `https://fundgz.1234567.com.cn/js/${fundCode}.js?rt=${Date.now()}`;
            const response = await axios.get(url, { 
                headers: {
                    ...this.headers,
                    'Referer': 'https://fund.eastmoney.com/'
                },
                timeout: 10000,
                responseType: 'text'
            });

            const data = response.data;
            
            // 检查是否是有效的JSONP响应
            if (!data || typeof data !== 'string' || !data.includes('jsonpgz')) {
                // fundgz 接口可能被风控（返回HTML反爬页面），回退到官方最新净值
                console.log(`基金 ${fundCode} 实时估值接口不可用，回退到最新公布净值`);
                return this._fallbackLatestNav(fundCode);
            }

            // 解析JSONP数据
            const jsonStr = data.replace(/^jsonpgz\\(/, '').replace(/\\);?\\s*$/, '');
            
            try {
                const estimateData = JSON.parse(jsonStr);
                
                return {
                    fund_code: fundCode,
                    fund_name: estimateData.name || `基金${fundCode}`,
                    estimate_nav: parseFloat(estimateData.gsz) || 0,
                    estimate_time: estimateData.gztime || '',
                    estimate_return: parseFloat(estimateData.gszzl) || 0,
                    last_nav: parseFloat(estimateData.dwjz) || 0,
                    last_date: estimateData.jzrq || '',
                    estimate_available: true
                };
            } catch (parseError) {
                console.log(`基金 ${fundCode} JSON解析失败:`, parseError.message);
                return this._fallbackLatestNav(fundCode);
            }
        } catch (error) {
            console.error(`获取基金 ${fundCode} 实时估值失败:`, error.message);
            return this._fallbackLatestNav(fundCode);
        }
    }
"""
new_head = """    /**
     * 基金 → 场内 ETF 代理映射（天天基金 fundgz 实时估值接口已于 2026-07-21 官方下线，
     * 使用跟踪同一/近似指数的场内 ETF 实时行情作为盘中估算）
     * 说明：精确=跟踪同一指数；近似=行业/风格相近，仅供盘中参考
     */
    static ETF_PROXY_MAP = {
        '161725': 'sh512690',   // 招商中证白酒 → 酒ETF（精确跟踪中证白酒）
        '005827': 'sz159928',   // 易方达蓝筹精选（白酒消费为主）→ 消费ETF（近似）
        '000001': 'sh510300',   // 华夏成长（大盘成长）→ 沪深300ETF（近似）
        '005267': 'sh510300'    // 嘉实价值精选（价值蓝筹）→ 沪深300ETF（近似）
    };

    /**
     * 通过场内 ETF 实时行情估算基金今日涨跌幅（新浪 hq.sinajs.cn，GBK 编码）
     * @param {string} fundCode 基金代码
     * @returns {Promise<Object|null>}
     */
    async _fetchEtfProxy(fundCode) {
        const etf = DataFetcher.ETF_PROXY_MAP[fundCode];
        if (!etf) return null;
        try {
            const url = `https://hq.sinajs.cn/list=${etf}`;
            const resp = await axios.get(url, {
                headers: {
                    ...this.headers,
                    'Referer': 'https://finance.sina.com.cn/',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                },
                timeout: 8000,
                responseType: 'arraybuffer'
            });
            const text = new TextDecoder('gbk').decode(Buffer.from(resp.data));
            const m = text.match(/="([^"]*)"/);
            if (!m) return null;
            const f = m[1].split(',');
            if (f.length < 32) return null;
            const price = parseFloat(f[3]);       // 当前价
            const prev = parseFloat(f[2]);        // 昨收
            if (!price || !prev) return null;
            const pct = (price / prev - 1) * 100;
            const fundName = await new Promise((resolve) => {
                this.db.get('SELECT fund_name FROM funds WHERE fund_code = ?', [fundCode], (err, row) => {
                    resolve(err || !row ? `基金${fundCode}` : row.fund_name);
                });
            });
            const dateStr = f[30] || '';
            const timeStr = f[31] || '';
            return {
                fund_code: fundCode,
                fund_name: fundName,
                estimate_nav: 0,
                estimate_time: (dateStr && timeStr) ? `${dateStr} ${timeStr}` : '',
                estimate_return: Math.round(pct * 100) / 100,
                last_nav: 0,
                last_date: dateStr,
                estimate_available: true,
                source: 'etf_proxy',
                note: `ETF代理估算（${etf} 实时行情，近似）`
            };
        } catch (e) {
            console.warn(`基金 ${fundCode} ETF代理估值失败:`, e.message);
            return null;
        }
    }

    /**
     * 获取基金实时估值（估算净值/估算涨跌幅）
     * 数据源顺序：① 场内ETF代理估值（新浪实时行情）→ ② fundgz（已官方下线，保留兼容）→ ③ 最新公布净值
     * @param {string} fundCode 基金代码
     * @returns {Promise<Object>} 实时估值数据
     */
    async getRealTimeEstimate(fundCode) {
        // ① ETF 代理估值（盘中实时）
        const etfEst = await this._fetchEtfProxy(fundCode);
        if (etfEst) return etfEst;

        // ② fundgz 实时估值（天天基金 2026-07-21 官方下线，可能返回 404 页，保留尝试）
        try {
            const url = `https://fundgz.1234567.com.cn/js/${fundCode}.js?rt=${Date.now()}`;
            const response = await axios.get(url, { 
                headers: {
                    ...this.headers,
                    'Referer': 'https://fund.eastmoney.com/'
                },
                timeout: 6000,
                responseType: 'text'
            });

            const data = response.data;
            if (!data || typeof data !== 'string' || !data.includes('jsonpgz')) {
                console.log(`基金 ${fundCode} fundgz 估值接口不可用，回退到最新公布净值`);
                return this._fallbackLatestNav(fundCode);
            }

            const jsonStr = data.replace(/^jsonpgz\\(/, '').replace(/\\);?\\s*$/, '');
            try {
                const estimateData = JSON.parse(jsonStr);
                return {
                    fund_code: fundCode,
                    fund_name: estimateData.name || `基金${fundCode}`,
                    estimate_nav: parseFloat(estimateData.gsz) || 0,
                    estimate_time: estimateData.gztime || '',
                    estimate_return: parseFloat(estimateData.gszzl) || 0,
                    last_nav: parseFloat(estimateData.dwjz) || 0,
                    last_date: estimateData.jzrq || '',
                    estimate_available: true
                };
            } catch (parseError) {
                console.log(`基金 ${fundCode} JSON解析失败:`, parseError.message);
                return this._fallbackLatestNav(fundCode);
            }
        } catch (error) {
            console.error(`获取基金 ${fundCode} 实时估值失败:`, error.message);
            return this._fallbackLatestNav(fundCode);
        }
    }
"""
assert c.count(old_head) == 1, 'head anchor count=%d' % c.count(old_head)
c = c.replace(old_head, new_head, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK data-fetcher.js 多源估值')
