@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [INFO] 正在启动 AI 量化智能体 Web 服务...
echo [INFO] 若 5000 端口被占用，会自动释放

' 调用静默启动脚本（独立进程，不会超时）
cscript //NoLogo "%~dp0run_web_silent.vbs"

if %errorlevel% neq 0 (
    echo [ERROR] 启动失败，请检查 Python 是否安装
    pause
    exit /b 1
)

echo [OK] 服务已启动，正在打开浏览器...
timeout /t 2 /nobreak >nul
