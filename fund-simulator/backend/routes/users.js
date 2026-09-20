/**
 * 用户路由：/api/users/*
 * 依赖通过 ctx 注入：{ db, userConfigs, getCurrentUser, setCurrentUser, getWatchlist, ensureFundWithNav }
 */
const { Router } = require('express');

module.exports = function usersRoutes(ctx) {
  const r = Router();
  const { db, userConfigs, getCurrentUser, setCurrentUser, getWatchlist, ensureFundWithNav } = ctx;

  r.get('/', async (req, res) => {
    const users = Object.values(userConfigs).map(u => ({
      id: u.id, name: u.name, avatar: u.avatar, style: u.style, description: u.description
    }));
    res.json(users);
  });

  r.get('/current', (req, res) => {
    const u = userConfigs[getCurrentUser()];
    res.json({
      id: u.id, name: u.name, avatar: u.avatar, style: u.style, description: u.description,
      risk_tolerance: u.risk_tolerance, target_return: u.target_return,
      stop_loss: u.stop_loss, max_position: u.max_position
    });
  });

  r.post('/switch', (req, res) => {
    const { user_id } = req.body;
    if (!userConfigs[user_id]) return res.status(404).json({ error: '用户不存在' });
    setCurrentUser(user_id);
    res.json({
      message: '切换成功',
      user: { id: userConfigs[user_id].id, name: userConfigs[user_id].name, avatar: userConfigs[user_id].avatar, style: userConfigs[user_id].style }
    });
  });

  r.get('/:id/watchlist', async (req, res) => {
    const { id } = req.params;
    if (!userConfigs[id]) return res.status(404).json({ error: '用户不存在' });
    try { res.json(await getWatchlist(id)); }
    catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.post('/:id/watchlist', async (req, res) => {
    const { id } = req.params;
    const { fund_code, reason } = req.body || {};
    if (!userConfigs[id]) return res.status(404).json({ error: '用户不存在' });
    if (!fund_code) return res.status(400).json({ error: '基金代码不能为空' });
    try {
      let fund = await new Promise((resolve, reject) => {
        db.get('SELECT fund_code FROM funds WHERE fund_code = ?', [fund_code], (e, row) => e ? reject(e) : resolve(row));
      });
      if (!fund) {
        const urow = await new Promise((resolve, reject) => {
          db.get('SELECT fund_code, fund_name, fund_type FROM fund_universe WHERE fund_code = ?', [fund_code], (e, row) => e ? reject(e) : resolve(row));
        });
        if (!urow) return res.status(404).json({ error: `基金 ${fund_code} 不在全市场基金库中` });
        const navN = await ensureFundWithNav({ fund_code: urow.fund_code, fund_name: urow.fund_name, fund_type: urow.fund_type });
        if (navN < 30) console.warn(`[手动观察] ${fund_code} 净值仅 ${navN} 条，信号可能不完整`);
      }
      await new Promise((resolve, reject) => {
        db.run('INSERT OR IGNORE INTO watchlist (user_id, fund_code, reason) VALUES (?, ?, ?)',
          [id, fund_code, reason || ''], e => e ? reject(e) : resolve());
      });
      res.json({ message: '已添加自选', watchlist: await getWatchlist(id) });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.delete('/:id/watchlist/:fundCode', async (req, res) => {
    const { id, fundCode } = req.params;
    if (!userConfigs[id]) return res.status(404).json({ error: '用户不存在' });
    try {
      // 只允许删除手动添加的，AI 推荐的不能删除
      const row = await new Promise((resolve, reject) => {
        db.get('SELECT source FROM watchlist WHERE user_id = ? AND fund_code = ?', [id, fundCode], (e, r) => e ? reject(e) : resolve(r));
      });
      if (!row) return res.status(404).json({ error: '基金不在观察池' });
      if (row.source === 'ai') return res.status(403).json({ error: 'AI 推荐的观察池不能删除，由 AI 维护' });
      await new Promise((resolve, reject) => {
        db.run('DELETE FROM watchlist WHERE user_id = ? AND fund_code = ?', [id, fundCode], e => e ? reject(e) : resolve());
      });
      res.json({ message: '已取消自选', watchlist: await getWatchlist(id) });
    } catch (e) { res.status(500).json({ error: e.message }); }
  });

  r.get('/:id/funds', (req, res) => {
    const { id } = req.params;
    if (!userConfigs[id]) return res.status(404).json({ error: '用户不存在' });
    res.json(userConfigs[id].fund_list);
  });

  r.get('/:id/config', (req, res) => {
    const { id } = req.params;
    if (!userConfigs[id]) return res.status(404).json({ error: '用户不存在' });
    res.json(userConfigs[id]);
  });

  return r;
};
