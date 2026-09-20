/**
 * 基金数据采集模块
 * 从天天基金网获取真实基金净值数据
 * 更新：使用正确的API端点和请求头
 */

const axios = require('axios');
const sqlite3 = require('sqlite3').verbose();

class FundDataFetcher {
    constructor() {
        this.db = new sqlite3.Database('./fund_simulator.db');
        this.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://fund.eastmoney.com/',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        };
    }

    /**
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
        const etf = FundDataFetcher.ETF_PROXY_MAP[fundCode];
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

            const jsonStr = data.replace(/^jsonpgz\(/, '').replace(/\);?\s*$/, '');
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

    /**
     * 实时估值不可用时的回退：返回最新公布净值（权威口径）
     * @param {string} fundCode 基金代码
     * @returns {Promise<Object|null>}
     */
    async _fallbackLatestNav(fundCode) {
        try {
            const navList = await this.getNavHistory(fundCode, '', '', 1);
            if (navList.length === 0) return null;
            const latest = navList[0];
            const fundName = await new Promise((resolve) => {
                this.db.get('SELECT fund_name FROM funds WHERE fund_code = ?', [fundCode], (err, row) => {
                    resolve(err || !row ? '' : row.fund_name);
                });
            });
            return {
                fund_code: fundCode,
                fund_name: fundName || `基金${fundCode}`,
                estimate_nav: latest.unit_nav,
                estimate_time: '',
                estimate_return: latest.daily_return || 0,
                last_nav: latest.unit_nav,
                last_date: latest.nav_date,
                estimate_available: false,
                note: '使用最新公布净值（无盘中估值）'
            };
        } catch (e) {
            console.error(`基金 ${fundCode} 回退获取最新净值失败:`, e.message);
            return null;
        }
    }

    /**
     * 获取基金历史净值（使用正确的API）
     * @param {string} fundCode 基金代码
     * @param {string} startDate 开始日期
     * @param {string} endDate 结束日期
     * @returns {Promise<Array>} 净值数据数组
     */
    async getNavHistory(fundCode, startDate = '', endDate = '', pageSize = 20, pageIndex = 1) {
        try {
            // 使用东方财富的历史净值API
            const apiUrl = `https://api.fund.eastmoney.com/f10/lsjz`;
            const params = {
                callback: 'jQuery18305498444533498498_' + Date.now(),
                fundCode: fundCode,
                pageIndex: pageIndex,
                pageSize: pageSize,
                startDate: startDate,
                endDate: endDate,
                _: Date.now()
            };

            const response = await axios.get(apiUrl, { 
                params,
                headers: {
                    ...this.headers,
                    'Referer': 'https://fundf10.eastmoney.com/'
                },
                timeout: 15000,
                responseType: 'text'
            });

            const jsonpData = response.data;
            
            // 检查响应格式
            if (!jsonpData || typeof jsonpData !== 'string') {
                console.log(`基金 ${fundCode} 历史数据响应异常`);
                return [];
            }

            // 解析JSONP响应
            const jsonStr = jsonpData.replace(/^[^(]*\(/, '').replace(/\);?\s*$/, '');
            
            try {
                const data = JSON.parse(jsonStr);

                if (!data || !data.Data || !data.Data.LSJZList || data.Data.LSJZList.length === 0) {
                    console.log(`基金 ${fundCode} 没有历史净值数据`);
                    return [];
                }

                const navList = data.Data.LSJZList.map(item => ({
                    fund_code: fundCode,
                    nav_date: item.FSRQ || '',
                    unit_nav: parseFloat(item.DWJZ) || 0,
                    acc_nav: parseFloat(item.LJJZ) || 0,
                    daily_return: parseFloat(item.JZZZL) || 0
                }));

                console.log(`✓ 获取到基金 ${fundCode} 的 ${navList.length} 条历史净值数据`);
                return navList;
            } catch (parseError) {
                console.log(`基金 ${fundCode} 历史数据JSON解析失败:`, parseError.message);
                return [];
            }

        } catch (error) {
            console.error(`获取基金 ${fundCode} 历史净值失败:`, error.message);
            return [];
        }
    }

    /**
     * 分页拉取完整历史净值（覆盖 startDate 至今，接口单页最多返回 20 条）
     * @param {string} fundCode 基金代码
     * @param {string} startDate 开始日期（含）
     * @param {string} endDate 结束日期
     * @param {number} maxPages 最大翻页数（默认 12 页 ≈ 240 个交易日 ≈ 一年）
     * @returns {Promise<Array>} 净值数据数组（按日期倒序）
     */
    async getNavHistoryAll(fundCode, startDate = '', endDate = '', maxPages = 12) {
        const all = [];
        for (let page = 1; page <= maxPages; page++) {
            const pageData = await this.getNavHistory(fundCode, startDate, endDate, 20, page);
            if (pageData.length === 0) break;
            all.push(...pageData);
            // 该页不足 20 条说明已翻到底
            if (pageData.length < 20) break;
            // 已覆盖到 startDate 之前则停止
            const oldest = pageData[pageData.length - 1].nav_date;
            if (startDate && oldest <= startDate) break;
            await new Promise(resolve => setTimeout(resolve, 200));
        }
        return all;
    }

    /**
     * 保存基金信息到数据库
     * @param {Object} fundInfo 基金信息
     */
    async saveFundInfo(fundInfo) {
        return new Promise((resolve, reject) => {
            const sql = `INSERT OR REPLACE INTO funds 
                (fund_code, fund_name, fund_type, inception_date, benchmark, manager) 
                VALUES (?, ?, ?, ?, ?, ?)`;
            
            this.db.run(sql, [
                fundInfo.fund_code,
                fundInfo.fund_name,
                fundInfo.fund_type || '',
                fundInfo.inception_date || '',
                fundInfo.benchmark || '',
                fundInfo.manager || ''
            ], function(err) {
                if (err) {
                    reject(err);
                } else {
                    resolve(this.changes);
                }
            });
        });
    }

    /**
     * 保存净值数据到数据库
     * @param {Array} navList 净值数据数组
     */
    async saveNavData(navList) {
        return new Promise((resolve, reject) => {
            if (!navList || navList.length === 0) {
                resolve(0);
                return;
            }

            const sql = `INSERT OR IGNORE INTO fund_nav 
                (fund_code, nav_date, unit_nav, acc_nav, daily_return) 
                VALUES (?, ?, ?, ?, ?)`;
            
            const stmt = this.db.prepare(sql);
            let insertCount = 0;

            this.db.serialize(() => {
                this.db.run('BEGIN TRANSACTION');
                
                navList.forEach(nav => {
                    stmt.run([
                        nav.fund_code,
                        nav.nav_date,
                        nav.unit_nav,
                        nav.acc_nav,
                        nav.daily_return
                    ], function(err) {
                        if (!err && this.changes > 0) {
                            insertCount++;
                        }
                    });
                });
                
                stmt.finalize();
                
                this.db.run('COMMIT', (err) => {
                    if (err) {
                        reject(err);
                    } else {
                        resolve(insertCount);
                    }
                });
            });
        });
    }

    /**
     * 获取全量基金列表（天天基金基金代码库）
     * 返回 [{fund_code, fund_name, fund_type, short_pinyin, pinyin}]
     * @returns {Promise<Array>}
     */
    async getFundList() {
        try {
            const url = 'https://fund.eastmoney.com/js/fundcode_search.js';
            const response = await axios.get(url, {
                headers: this.headers,
                timeout: 20000,
                responseType: 'text'
            });

            const text = response.data;
            const match = text.match(/var r = (\[.*\]);?/s);
            if (!match) {
                console.error('基金列表解析失败：未找到数组数据');
                return [];
            }

            const rows = JSON.parse(match[1]);
            return rows.map(row => ({
                fund_code: row[0],
                short_pinyin: row[1],
                fund_name: row[2],
                fund_type: row[3],
                pinyin: row[4]
            }));
        } catch (error) {
            console.error('获取基金列表失败:', error.message);
            return [];
        }
    }

    /**
     * 批量采集基金数据（历史净值 + 入库）
     * 供 /update-fund-data 与种子脚本使用
     * @param {Array<string>} fundCodes 基金代码数组
     * @param {string} startDate 开始日期
     * @param {string} endDate 结束日期
     * @param {number} pageSize 每页条数
     * @returns {Promise<Object>} 采集汇总
     */
    async batchFetchFundData(fundCodes, startDate = '', endDate = '', pageSize = 30) {
        const results = [];
        for (const code of fundCodes) {
            try {
                // 给定日期范围时翻页拉全，否则拉最近一页
                const navList = startDate
                    ? await this.getNavHistoryAll(code, startDate, endDate, 12)
                    : await this.getNavHistory(code, '', endDate, pageSize);
                let inserted = 0;
                if (navList.length > 0) {
                    inserted = await this.saveNavData(navList);
                }
                results.push({
                    fund_code: code,
                    fetched: navList.length,
                    inserted: inserted,
                    ok: true
                });
                // 避免请求过快触发风控
                await new Promise(resolve => setTimeout(resolve, 300));
            } catch (e) {
                results.push({ fund_code: code, fetched: 0, inserted: 0, ok: false, error: e.message });
            }
        }
        return results;
    }

    /**
     * 获取热门基金（精选知名基金，带最新净值快照）
     * @param {number} limit 返回数量
     * @returns {Promise<Array>}
     */
    async getPopularFunds(limit = 20) {
        const popularCodes = [
            '110011', '161725', '005827', '003834', '005267', // 默认用户持仓/关注
            '260108', '320007', '001156', '001938', '519736', // 激进用户持仓/关注
            '000961', '000001', '000011', '000041', '001015', '002001', '002011' // 观察池
        ];
        const list = popularCodes.slice(0, limit);
        const result = [];
        for (const code of list) {
            const estimate = await this.getRealTimeEstimate(code);
            if (estimate) {
                result.push({ ...estimate });
            }
            await new Promise(resolve => setTimeout(resolve, 300));
        }
        return result;
    }

    /**
     * 关闭数据库连接
     */
    close() {
        this.db.close();
    }
}

module.exports = FundDataFetcher;