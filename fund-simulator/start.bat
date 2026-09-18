@echo off
echo ========================================
echo   基金模拟交易系统 - 启动脚本
echo ========================================
echo.

echo [1/2] 启动后端服务器...
start "基金模拟系统-后端" cmd /k "cd /d %~dp0 && node server.js"

echo [2/2] 启动前端开发服务器...
timeout /t 3 /nobreak >nul
start "基金模拟系统-前端" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo.
echo ========================================
echo   系统启动完成！
echo   前端地址: http://localhost:5173
echo   后端地址: http://localhost:3000
echo ========================================
pause