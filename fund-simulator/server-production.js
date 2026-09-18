const express = require('express');
const path = require('path');
const history = require('connect-history-api-fallback');
const app = express();
const PORT = process.env.PORT || 3000;

// 中间件
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// API路由（需要在静态文件之前）
app.use('/api', require('./api/routes'));

// Vue Router的history模式支持
app.use(history());

// 提供Vue构建后的静态文件
app.use(express.static(path.join(__dirname, 'frontend/dist')));

// 所有其他请求返回Vue的index.html（Express 5 不再支持 app.get('*')，改用兜底中间件）
app.use((req, res) => {
  res.sendFile(path.join(__dirname, 'frontend/dist', 'index.html'));
});

// 错误处理中间件
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: '服务器内部错误' });
});

// 启动服务器
app.listen(PORT, () => {
  console.log(`基金模拟系统运行在 http://localhost:${PORT}`);
  console.log(`环境: ${process.env.NODE_ENV || 'development'}`);
});

// 优雅关闭
process.on('SIGINT', () => {
  console.log('服务器正在关闭...');
  process.exit(0);
});