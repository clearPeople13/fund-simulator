// P1 patch B：接入 close 流程（评分/市场/分红/再平衡/换仓/归因/压力/复盘）+ 研究笔记 + API
const fs = require('fs');
const p = 'C:/Users/jiancent/WorkBuddy/fund/fund-simulator/server.js';
let s = fs.readFileSync(p, 'utf8');
const fail = (m) => { console.error('FAIL: ' + m); process.exit(1); };

// R1: 研究笔记写入（performAnalysis 内"保存分析记录"后）
{
  const anchor = "        console.log(`  ${fundCode}: ${decision} (信号:${action}) 当前:¥${currentNav} 日涨跌:${dailyReturn}%`);";
  if (!s.includes(anchor)) fail('R1 锚点未找到');
  const inject = `        // ===== P1：研究笔记（决策依据/理由/指标，前端可读）=====
        if (currentNav > 0) {
          db.run('INSERT INTO research_notes (user_id, fund_code, analysis_type, signal, reason, metrics) VALUES (?, ?, ?, ?, ?, ?)',
            [userId, fundCode, analysisType, action, sig.signal.reason || decision,
             JSON.stringify({ nav: currentNav, daily: dailyReturn, change_20d: sig.change_20d, drawdown_60d: sig.drawdown_60d })], (err) => {
              if (err) console.error('研究笔记写入失败:', err.message);
            });
        }

        console.log(\`  \${fundCode}: \${decision} (信号:\${action}) 当前:¥\${currentNav} 日涨跌:\${dailyReturn}%\`);`;
  s = s.replace(anchor, inject);
}

// R2: close 末尾 P1 接入（在 P0-3 块后）
{
  const anchor = "    console.log(`\\n=== ${typeNames[analysisType]}完成 ===\\n`);";
  if (!s.includes(anchor)) fail('R2 锚点未找到');
  const inject = `    // ===== P1：评分/市场温度/分红/再平衡/换仓/归因/压力/复盘 =====
    if (analysisType === 'close') {
      const now = new Date();
      const dayOfWeek = now.getDay();
      const isLastTradingDayOfMonth = dayOfWeek === 5 && (now.getDate() + 7 > new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate());
      try { await computeMarketEnv(); } catch (e) { console.error('[市场温度] 失败:', e.message); }
      // 每周五更新基金评分画像
      if (dayOfWeek === 5) { try { await computeFundProfiles(); } catch (e) { console.error('[评分] 失败:', e.message); } }
      // 每月初同步分红记录
      if (now.getDate() <= 3) { try { await dividendAdjust(); } catch (e) { console.error('[分红] 失败:', e.message); } }
      for (const userId of Object.keys(userConfigs)) {
        try {
          const cfg = await getRiskParams(userId);
          // 再平衡（weekly 每周五 / monthly 月末）
          if ((cfg.rebalance_frequency === 'weekly' && dayOfWeek === 5) || (cfg.rebalance_frequency === 'monthly' && isLastTradingDayOfMonth)) {
            await rebalanceCheck(userId);
          }
          // 换仓评估（每周五）
          if (dayOfWeek === 5) { await switchFunds(userId); }
          // 业绩归因（月末）→ 追加到月报
          if (isLastTradingDayOfMonth) {
            try { const attr = await performanceAttribution(userId); if (attr) console.log(\`[归因] \${userId} 配置贡献\${attr.allocation}% 选基贡献\${attr.selection}% 总超额\${attr.totalExcess}%\`); } catch (e) { console.error('[归因] 失败:', e.message); }
            try { await generatePressureReport(userId); console.log(\`[压力] \${userId} 压力测试报告已生成\`); } catch (e) { console.error('[压力] 失败:', e.message); }
          }
        } catch (p1Err) { console.error(\`[P1] \${userId} 失败:\`, p1Err.message); }
      }
      // 每日复盘（每日收盘后）
      try { await generateDailyRecap(); } catch (e) { console.error('[复盘] 失败:', e.message); }
    }

    console.log(\`\\n=== \${typeNames[analysisType]}完成 ===\\n\`);`;
  s = s.replace(anchor, inject);
}

// R3: API（profile / research / reports/:id / alerts / market-env / recap）
{
  const anchor = "app.get('/api/risk/events', (req, res) => {";
  if (!s.includes(anchor)) fail('R3 锚点未找到');
  const apis = `app.get('/api/funds/:code/profile', (req, res) => {
  db.get('SELECT * FROM fund_profiles WHERE fund_code = ?', [req.params.code], (err, row) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ profile: row || null });
  });
});

app.get('/api/funds/:code/research', (req, res) => {
  const userId = req.query.user_id || currentUser;
  const limit = Math.min(parseInt(req.query.limit) || 20, 100);
  db.all('SELECT * FROM research_notes WHERE user_id = ? AND fund_code = ? ORDER BY id DESC LIMIT ?', [userId, req.params.code, limit], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ notes: rows || [] });
  });
});

app.get('/api/alerts', (req, res) => {
  const userId = req.query.user_id || currentUser;
  const limit = Math.min(parseInt(req.query.limit) || 50, 200);
  db.all('SELECT * FROM risk_events WHERE user_id = ? ORDER BY id DESC LIMIT ?', [userId, limit], (err, events) => {
    if (err) return res.status(500).json({ error: err.message });
    db.all('SELECT * FROM data_quality_logs ORDER BY id DESC LIMIT 20', [], (err2, dq) => {
      if (err2) return res.status(500).json({ error: err2.message });
      res.json({ events: events || [], data_quality: dq || [] });
    });
  });
});

app.get('/api/market-env', (req, res) => {
  db.all('SELECT * FROM market_env ORDER BY date DESC LIMIT 30', [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ market: rows || [] });
  });
});

app.get('/api/daily-recap', (req, res) => {
  const userId = req.query.user_id || currentUser;
  db.all('SELECT * FROM reports WHERE user_id = ? AND report_type = ? ORDER BY id DESC LIMIT 7', [userId, 'daily'], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ recaps: rows || [] });
  });
});

app.get('/api/reports/:id', (req, res) => {
  db.get('SELECT * FROM reports WHERE id = ?', [req.params.id], (err, row) => {
    if (err) return res.status(500).json({ error: err.message });
    if (!row) return res.status(404).json({ error: '报告不存在' });
    res.json({ report: row });
  });
});

app.get('/api/risk/events', (req, res) => {`;
  s = s.replace(anchor, apis);
}

fs.writeFileSync(p, s, 'utf8');
console.log('P1 patch B 完成，新长度:', s.length);
