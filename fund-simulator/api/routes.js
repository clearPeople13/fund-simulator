const express = require('express');
const router = express.Router();
const sqlite3 = require('sqlite3').verbose();
const FundDataFetcher = require('../data-fetcher');

// 数据库连接
const db = new sqlite3.Database('./fund_simulator.db');
const fetcher = new FundDataFetcher();

// 基金相关路由

// 获取基金列表（全市场基金库 fund_universe，与 AI 观察池/持仓独立）
router.get('/funds', (req, res) => {
  const { type, sort, order, page = 1, limit = 20, keyword } = req.query;

  const where = [];
  const params = [];
  if (type) {
    where.push('u.fund_type = ?');
    params.push(type);
  }
  if (keyword) {
    const kw = '%' + String(keyword) + '%';
    where.push('(u.fund_code LIKE ? OR u.fund_name LIKE ?)');
    params.push(kw, kw);
  }
  const whereSql = where.length ? ' WHERE ' + where.join(' AND ') : '';

  // 排序白名单：支持按涨幅/净值/代码排序
  const sortMap = {
    fund_code: 'u.fund_code', fund_name: 'u.fund_name',
    day_return: 'u.day_return', r1w: 'u.r1w', r1m: 'u.r1m', r3m: 'u.r3m', r6m: 'u.r6m',
    r1y: 'u.r1y', r2y: 'u.r2y', r3y: 'u.r3y', ytd: 'u.ytd', since: 'u.since',
    unit_nav: 'u.unit_nav', scale: 'u.scale'
  };
  const sortCol = sortMap[sort] || 'u.r6m';
  const sortDir = order === 'asc' ? 'ASC' : 'DESC';

  const offset = (parseInt(page) - 1) * parseInt(limit);
  const query = `SELECT u.fund_code, u.fund_name, u.fund_type, u.unit_nav AS latest_nav, u.nav_date AS latest_nav_date,
        u.day_return, u.r1w, u.r1m, u.r3m, u.r6m AS recent_return, u.r1y, u.r2y, u.r3y, u.ytd, u.since, u.inception_date, u.scale
      FROM fund_universe u${whereSql}
      ORDER BY ${sortCol} ${sortDir} LIMIT ? OFFSET ?`;
  params.push(parseInt(limit), offset);

  db.all(query, params, (err, rows) => {
    if (err) { res.status(500).json({ error: err.message }); return; }
    const countQuery = `SELECT COUNT(*) AS total FROM fund_universe u${whereSql}`;
    db.get(countQuery, where.length ? params.slice(0, params.length - 2) : [], (err2, countRow) => {
      if (err2) { res.status(500).json({ error: err2.message }); return; }
      res.json({
        data: rows,
        pagination: { page: parseInt(page), limit: parseInt(limit), total: countRow.total }
      });
    });
  });
});

router.get('/funds/:code', (req, res) => {
  const { code } = req.params;

  db.get('SELECT * FROM funds WHERE fund_code = ?', [code], (err, row) => {
    if (err) { res.status(500).json({ error: err.message }); return; }
    if (row) { res.json(row); return; }

    // 全市场基金库兜底：未纳入跟踪的新基金也返回基础信息
    db.get('SELECT fund_code, fund_name, fund_type, unit_nav AS latest_nav, nav_date AS latest_nav_date, day_return, r6m AS recent_return, inception_date, scale FROM fund_universe WHERE fund_code = ?', [code], (err2, urow) => {
      if (err2) { res.status(500).json({ error: err2.message }); return; }
      if (!urow) { res.status(404).json({ error: '基金不存在' }); return; }
      res.json({ ...urow, tracked: false });
    });
  });
});

// 历史分红明细（由累计净值-单位净值跳变推导，dividends 表）
router.get('/funds/:code/dividends', (req, res) => {
  const { code } = req.params;
  const limit = Math.min(parseInt(req.query.limit || '20', 10) || 20, 200);
  db.all('SELECT ex_date, per_unit, type FROM dividends WHERE fund_code = ? ORDER BY ex_date DESC LIMIT ?', [code, limit], (err, rows) => {
    if (err) { res.status(500).json({ error: err.message }); return; }
    db.get('SELECT COUNT(*) AS total FROM dividends WHERE fund_code = ?', [code], (err2, cnt) => {
      if (err2) { res.status(500).json({ error: err2.message }); return; }
      res.json({ fund_code: code, total: cnt ? cnt.total : 0, list: rows || [] });
    });
  });
});

// 获取基金净值历史
router.get('/funds/:code/nav', async (req, res) => {
  const { code } = req.params;
  const { start_date, end_date, limit = 100 } = req.query;
  
  try {
    // 先从数据库查询
    let query = 'SELECT * FROM fund_nav WHERE fund_code = ?';
    const params = [code];
    
    if (start_date) {
      query += ' AND nav_date >= ?';
      params.push(start_date);
    }
    
    if (end_date) {
      query += ' AND nav_date <= ?';
      params.push(end_date);
    }
    
    query += ' ORDER BY nav_date DESC LIMIT ?';
    params.push(parseInt(limit));
    
    db.all(query, params, async (err, rows) => {
      if (err) {
        res.status(500).json({ error: err.message });
        return;
      }
      
      // 如果数据库中没有数据，从网络获取
      if (rows.length === 0) {
        try {
          const navData = await fetcher.getNavHistory(code, start_date, end_date);
          if (navData.length > 0) {
            // 保存到数据库
            await fetcher.saveNavData(navData);
            res.json(navData.slice(0, limit));
          } else {
            res.json([]);
          }
        } catch (fetchError) {
          res.status(500).json({ error: '获取净值数据失败: ' + fetchError.message });
        }
      } else {
        res.json(rows);
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 获取基金区间涨跌幅（支付宝式：近1月/近3月/近6月/近1年/近3年/成立来）
router.get('/funds/:code/returns', (req, res) => {
  const { code } = req.params;
  db.all(
    'SELECT nav_date, unit_nav FROM fund_nav WHERE fund_code = ? ORDER BY nav_date ASC',
    [code],
    (err, rows) => {
      if (err) { res.status(500).json({ error: err.message }); return; }
      if (!rows.length) { res.json({ fund_code: code, periods: [] }); return; }
      const last = rows.length - 1;
      const latestNav = rows[last].unit_nav;
      const latestDate = rows[last].nav_date;
      const calc = (idx) => (idx < 0 || idx >= rows.length ? null : (latestNav / rows[idx].unit_nav - 1) * 100);
      const defs = [
        { label: '近1月', idx: last - 22 },
        { label: '近3月', idx: last - 66 },
        { label: '近6月', idx: last - 132 },
        { label: '近1年', idx: last - 250 },
        { label: '近3年', idx: last - 750 },
        { label: '成立来', idx: 0 }
      ];
      const periods = defs.map(d => ({
        label: d.label,
        value: d.idx < 0 ? null : Number(calc(d.idx).toFixed(2)),
        start_date: (d.idx >= 0 && rows[d.idx]) ? rows[d.idx].nav_date : null,
        end_date: latestDate
      }));
      res.json({ fund_code: code, latest_nav: latestNav, latest_date: latestDate, periods });
    }
  );
});

// 获取基金实时估值
router.get('/funds/:code/estimate', async (req, res) => {
  const { code } = req.params;
  
  try {
    const estimate = await fetcher.getRealTimeEstimate(code);
    if (estimate) {
      res.json(estimate);
    } else {
      res.status(404).json({ error: '无法获取实时估值' });
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 批量获取持仓基金实时估值（预估今日涨幅）
router.get('/portfolio/estimates', async (req, res) => {
  const codes = String(req.query.codes || '').split(',').map(s => s.trim()).filter(Boolean);
  if (!codes.length) { res.json({}); return; }
  const out = {};
  for (const code of codes) {
    try {
      const e = await fetcher.getRealTimeEstimate(code);
      out[code] = e ? {
        estimate_return: e.estimate_return,
        estimate_time: e.estimate_time || '',
        estimate_available: !!e.estimate_available,
        estimate_nav: e.estimate_nav || 0
      } : null;
    } catch (err) {
      out[code] = null;
    }
    await new Promise(r => setTimeout(r, 120));
  }
  res.json(out);
});

// 投资组合相关路由

// 获取投资组合列表
router.get('/portfolios', (req, res) => {
  db.all('SELECT * FROM portfolios', [], (err, rows) => {
    if (err) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.json(rows);
  });
});

// 创建投资组合
router.post('/portfolios', (req, res) => {
  const { portfolio_name, initial_capital } = req.body;
  
  if (!portfolio_name) {
    return res.status(400).json({ error: '组合名称不能为空' });
  }
  
  const sql = 'INSERT INTO portfolios (portfolio_name, initial_capital, current_capital) VALUES (?, ?, ?)';
  db.run(sql, [portfolio_name, initial_capital || 100000, initial_capital || 100000], function(err) {
    if (err) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.json({ id: this.lastID, message: '投资组合创建成功' });
  });
});

// 获取持仓信息
router.get('/portfolios/:id/holdings', (req, res) => {
  const { id } = req.params;
  
  const sql = `
    SELECT h.*, f.fund_name, f.fund_type 
    FROM holdings h 
    LEFT JOIN funds f ON h.fund_code = f.fund_code 
    WHERE h.portfolio_id = ?
    ORDER BY h.market_value DESC
  `;
  
  db.all(sql, [id], (err, rows) => {
    if (err) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.json(rows);
  });
});

// 模拟交易 - 买入基金
router.post('/portfolios/:id/buy', async (req, res) => {
  const { id } = req.params;
  const { fund_code, amount } = req.body;
  
  if (!fund_code || !amount || amount <= 0) {
    return res.status(400).json({ error: '基金代码和金额不能为空' });
  }
  
  try {
    // 获取最新净值
    const navData = await fetcher.getNavHistory(fund_code, '', '', 1);
    if (!navData || navData.length === 0) {
      return res.status(404).json({ error: '未找到基金净值数据' });
    }
    
    const price = navData[0].unit_nav;
    const shares = amount / price;
    const fees = amount * 0.0015; // 假设申购费率0.15%
    
    // 更新持仓
    db.get('SELECT * FROM holdings WHERE portfolio_id = ? AND fund_code = ?', [id, fund_code], (err, holding) => {
      if (err) {
        res.status(500).json({ error: err.message });
        return;
      }
      
      if (holding) {
        // 更新现有持仓
        const newShares = holding.shares + shares;
        const newCost = (holding.cost_price * holding.shares + amount) / newShares;
        
        db.run('UPDATE holdings SET shares = ?, cost_price = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', 
          [newShares, newCost, holding.id], function(err) {
            if (err) {
              res.status(500).json({ error: err.message });
              return;
            }
            
            // 记录交易
            db.run('INSERT INTO transactions (portfolio_id, fund_code, transaction_type, amount, price, shares, fees) VALUES (?, ?, ?, ?, ?, ?, ?)',
              [id, fund_code, 'BUY', amount, price, shares, fees], function(err) {
                if (err) {
                  res.status(500).json({ error: err.message });
                  return;
                }
                
                res.json({ 
                  message: '买入成功',
                  transaction_id: this.lastID,
                  shares: shares,
                  price: price,
                  fees: fees
                });
              });
          });
      } else {
        // 创建新持仓
        db.run('INSERT INTO holdings (portfolio_id, fund_code, shares, cost_price, current_price, market_value, profit_loss, profit_loss_rate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
          [id, fund_code, shares, price, price, amount, 0, 0], function(err) {
            if (err) {
              res.status(500).json({ error: err.message });
              return;
            }
            
            // 记录交易
            db.run('INSERT INTO transactions (portfolio_id, fund_code, transaction_type, amount, price, shares, fees) VALUES (?, ?, ?, ?, ?, ?, ?)',
              [id, fund_code, 'BUY', amount, price, shares, fees], function(err) {
                if (err) {
                  res.status(500).json({ error: err.message });
                  return;
                }
                
                res.json({ 
                  message: '买入成功',
                  transaction_id: this.lastID,
                  shares: shares,
                  price: price,
                  fees: fees
                });
              });
          });
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 获取交易记录
router.get('/portfolios/:id/transactions', (req, res) => {
  const { id } = req.params;
  
  const sql = `
    SELECT t.*, f.fund_name 
    FROM transactions t 
    LEFT JOIN funds f ON t.fund_code = f.fund_code 
    WHERE t.portfolio_id = ?
    ORDER BY t.transaction_date DESC
  `;
  
  db.all(sql, [id], (err, rows) => {
    if (err) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.json(rows);
  });
});

// 获取组合表现
router.get('/portfolios/:id/performance', async (req, res) => {
  const { id } = req.params;
  
  try {
    // 获取持仓
    const holdings = await new Promise((resolve, reject) => {
      db.all('SELECT * FROM holdings WHERE portfolio_id = ?', [id], (err, rows) => {
        if (err) reject(err);
        else resolve(rows);
      });
    });
    
    // 获取初始资金
    const portfolio = await new Promise((resolve, reject) => {
      db.get('SELECT * FROM portfolios WHERE id = ?', [id], (err, row) => {
        if (err) reject(err);
        else resolve(row);
      });
    });
    
    // 计算当前总资产
    let totalAssets = portfolio.initial_capital;
    let totalCost = 0;
    
    holdings.forEach(holding => {
      totalCost += holding.cost_price * holding.shares;
      totalAssets += holding.market_value - (holding.cost_price * holding.shares);
    });
    
    const totalReturn = totalAssets - portfolio.initial_capital;
    const totalReturnRate = (totalReturn / portfolio.initial_capital) * 100;
    
    res.json({
      initial_capital: portfolio.initial_capital,
      current_assets: totalAssets,
      total_return: totalReturn,
      total_return_rate: totalReturnRate,
      holdings_count: holdings.length
    });
    
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 数据更新路由
router.post('/update-fund-data', async (req, res) => {
  const { fund_codes, start_date, end_date } = req.body;
  
  if (!fund_codes || !Array.isArray(fund_codes)) {
    return res.status(400).json({ error: '请提供基金代码数组' });
  }
  
  try {
    const results = await fetcher.batchFetchFundData(fund_codes, start_date, end_date);
    res.json({
      message: '数据更新完成',
      results: results
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 热门基金
router.get('/popular-funds', async (req, res) => {
  try {
    const funds = await fetcher.getPopularFunds();
    res.json(funds);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;