import io

# 1) readonly.js 加 /analysis/logs 和 /analysis/latest
p1 = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\routes\readonly.js"
with io.open(p1, 'r', encoding='utf-8') as f:
    s1 = f.read()
old = "  r.get('/ai/stats', async (req, res) => {"
new = """  r.get('/analysis/logs', async (req, res) => {
    try {
      const userId = req.query.user_id || getCurrentUser();
      const analysisType = req.query.type;
      const limit = parseInt(req.query.limit) || 50;
      let sql = 'SELECT * FROM analysis_logs WHERE user_id = ?';
      const params = [userId];
      if (analysisType) { sql += ' AND analysis_type = ?'; params.push(analysisType); }
      sql += ' ORDER BY analysis_time DESC LIMIT ?';
      params.push(limit);
      db.all(sql, params, (e, rows) => {
        if (e) return res.status(500).json({ error: e.message });
        res.json(rows);
      });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.get('/analysis/latest', async (req, res) => {
    try {
      const userId = req.query.user_id || getCurrentUser();
      const sql = `SELECT al.* FROM analysis_logs al
        INNER JOIN (SELECT fund_code, MAX(analysis_time) as max_time FROM analysis_logs WHERE user_id = ? GROUP BY fund_code
        ) latest ON al.fund_code = latest.fund_code AND al.analysis_time = latest.max_time
        WHERE al.user_id = ?`;
      db.all(sql, [userId, userId], (e, rows) => {
        if (e) return res.status(500).json({ error: e.message });
        let totalEstimatedPnl = 0;
        rows.forEach(row => { totalEstimatedPnl += row.estimated_pnl || 0; });
        res.json({
          funds: rows,
          total_estimated_pnl: totalEstimatedPnl.toFixed(2),
          last_update: rows.length > 0 ? rows[0].analysis_time : null
        });
      });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.get('/ai/stats', async (req, res) => {"""
assert s1.count(old) == 1
s1 = s1.replace(old, new)
with io.open(p1, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s1)

# 2) server.js 删 /api/analysis/logs + /api/analysis/latest 块
p2 = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p2, 'r', encoding='utf-8') as f:
    s2 = f.read()
start = s2.find("app.get('/api/analysis/logs', async (req, res) => {")
assert start != -1
end = s2.find("// 分析记录表（存档）", start)
assert end != -1
s2 = s2[:start] + "// /api/analysis/logs + /api/analysis/latest 已抽到 routes/readonly.js\n" + s2[end:]
with io.open(p2, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s2)
print('analysis logs+latest moved')
