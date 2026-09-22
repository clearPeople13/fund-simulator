// AI 角色管理路由：增删改查角色配置
// ctx: { db, userConfigs, getCurrentUser, setCurrentUser }
module.exports = function({ db, userConfigs, getCurrentUser, setCurrentUser }) {
  const router = require('express').Router();

  // 列出所有角色
  router.get('/', (req, res) => {
    db.all('SELECT * FROM ai_roles ORDER BY created_at', (err, rows) => {
      if (err) return res.status(500).json({ error: err.message });
      // 解析 base_weights
      const roles = rows.map(r => {
        let bw = {};
        try { bw = JSON.parse(r.base_weights || '{}'); } catch(e) {}
        return { ...r, base_weights: bw };
      });
      res.json({ roles, current: getCurrentUser() });
    });
  });

  // 添加新角色
  router.post('/', (req, res) => {
    const {
      name, avatar = '🤖', style = '稳健型', description = '',
      initial_capital = 100000, risk_tolerance = 'medium', target_return = 0.10,
      stop_loss, take_profit, max_position, max_single_fund, min_hold_funds,
      max_drawdown, exit_drawdown, exit_style = 'timely',
      entry_signal_threshold = 'strong', buy_ratio = 0.2, add_ratio = 0.1,
      add_cooldown_days = 5, rebalance_frequency = 'monthly',
      watchlist_style = '均衡分散/大盘蓝筹', base_weights = {}
    } = req.body;

    if (!name) return res.status(400).json({ error: '角色名称不能为空' });

    const id = 'role_' + Date.now().toString(36);
    
    // 根据风格自动填默认参数（如果没传）
    const isAggressive = style === '激进型' || style === 'aggressive';
    const defaults = isAggressive ? {
      stop_loss: 0.10, take_profit: 0.40, max_position: 1.00,
      max_single_fund: 0.40, min_hold_funds: 2, max_drawdown: 0.20,
      exit_drawdown: 25, entry_signal_threshold: 'medium',
      add_cooldown_days: 3, rebalance_frequency: 'weekly',
      watchlist_style: '成长/主题/高弹性',
      base_weights: base_weights || { '混合型': 0.4, '股票型': 0.5, '指数型': 0.1 }
    } : {
      stop_loss: 0.05, take_profit: 0.20, max_position: 0.60,
      max_single_fund: 0.20, min_hold_funds: 3, max_drawdown: 0.10,
      exit_drawdown: 15, entry_signal_threshold: 'strong',
      add_cooldown_days: 5, rebalance_frequency: 'monthly',
      watchlist_style: '均衡分散/大盘蓝筹',
      base_weights: base_weights || { '混合型': 0.5, '股票型': 0.3, '指数型': 0.2 }
    };

    const params = {
      stop_loss: stop_loss ?? defaults.stop_loss,
      take_profit: take_profit ?? defaults.take_profit,
      max_position: max_position ?? defaults.max_position,
      max_single_fund: max_single_fund ?? defaults.max_single_fund,
      min_hold_funds: min_hold_funds ?? defaults.min_hold_funds,
      max_drawdown: max_drawdown ?? defaults.max_drawdown,
      exit_drawdown: exit_drawdown ?? defaults.exit_drawdown,
      entry_signal_threshold: entry_signal_threshold ?? defaults.entry_signal_threshold,
      add_cooldown_days: add_cooldown_days ?? defaults.add_cooldown_days,
      rebalance_frequency: rebalance_frequency ?? defaults.rebalance_frequency,
      watchlist_style: watchlist_style ?? defaults.watchlist_style,
      base_weights: JSON.stringify(defaults.base_weights)
    };

    db.run(`INSERT INTO ai_roles 
      (id, name, avatar, style, description, initial_capital, risk_tolerance, target_return,
       stop_loss, take_profit, max_position, max_single_fund, min_hold_funds, max_drawdown,
       exit_drawdown, exit_style, entry_signal_threshold, buy_ratio, add_ratio, add_cooldown_days,
       rebalance_frequency, watchlist_style, base_weights)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [id, name, avatar, style, description, initial_capital, risk_tolerance, target_return,
       params.stop_loss, params.take_profit, params.max_position, params.max_single_fund,
       params.min_hold_funds, params.max_drawdown, params.exit_drawdown, exit_style,
       params.entry_signal_threshold, buy_ratio, add_ratio, params.add_cooldown_days,
       params.rebalance_frequency, params.watchlist_style, params.base_weights],
      function(err) {
        if (err) return res.status(500).json({ error: err.message });
        
        // 同步到内存 userConfigs
        userConfigs[id] = {
          id, name, avatar, style, description,
          initial_capital, risk_tolerance, target_return,
          ...params,
          buy_ratio, add_ratio, exit_style,
          fund_list: [], watchlist: []
        };
        
        res.json({ success: true, id, message: `角色「${name}」已创建` });
      });
  });

  // 修改角色
  router.put('/:id', (req, res) => {
    const { id } = req.params;
    const updates = req.body;
    
    const allowedFields = ['name', 'avatar', 'style', 'description', 'initial_capital',
      'risk_tolerance', 'target_return', 'stop_loss', 'take_profit', 'max_position',
      'max_single_fund', 'min_hold_funds', 'max_drawdown', 'exit_drawdown', 'exit_style',
      'entry_signal_threshold', 'buy_ratio', 'add_ratio', 'add_cooldown_days',
      'rebalance_frequency', 'watchlist_style'];
    
    const setClauses = [];
    const values = [];
    for (const [k, v] of Object.entries(updates)) {
      if (allowedFields.includes(k)) {
        setClauses.push(`${k} = ?`);
        values.push(v);
      }
    }
    if (updates.base_weights) {
      setClauses.push('base_weights = ?');
      values.push(JSON.stringify(updates.base_weights));
    }
    if (setClauses.length === 0) return res.status(400).json({ error: '没有要更新的字段' });
    
    values.push(id);
    db.run(`UPDATE ai_roles SET ${setClauses.join(', ')} WHERE id = ?`, values, function(err) {
      if (err) return res.status(500).json({ error: err.message });
      
      // 同步到内存
      if (userConfigs[id]) {
        Object.assign(userConfigs[id], updates);
        if (updates.base_weights) userConfigs[id].base_weights = updates.base_weights;
      }
      
      res.json({ success: true, message: '角色已更新' });
    });
  });

  // 删除角色
  router.delete('/:id', (req, res) => {
    const { id } = req.params;
    if (id === 'default' || id === 'aggressive') {
      return res.status(400).json({ error: '默认角色不能删除' });
    }
    
    db.run('DELETE FROM ai_roles WHERE id = ?', [id], function(err) {
      if (err) return res.status(500).json({ error: err.message });
      
      // 从内存删除
      delete userConfigs[id];
      
      // 如果删除的是当前用户，切回 default
      if (getCurrentUser() === id) setCurrentUser('default');
      
      res.json({ success: true, message: '角色已删除' });
    });
  });

  return router;
};
