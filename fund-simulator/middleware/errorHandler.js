/** 统一错误处理中间件（4 参数 Express 约定） */
function errorHandler(err, req, res, next) {
  console.error('[ERR]', req.method, req.url, err.message);
  if (res.headersSent) return next(err);
  res.status(err.status || 500).json({ ok: false, error: err.message || '服务器内部错误' });
}

/** async 路由包装器：收拢 try/catch，错误交给 errorHandler */
const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

module.exports = { errorHandler, asyncHandler };
