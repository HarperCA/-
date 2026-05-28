@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================
echo    🌐 AI 量化智能体 - 公网隧道启动器
echo ==========================================
echo.

:: 检查 Web 服务是否运行
echo [1/3] 检查本地 Web 服务...
tasklist | findstr "pythonw" >nul
if %errorlevel% neq 0 (
    echo [!] Web 服务未运行，正在启动...
    wscript //NoLogo "%~dp0run_web_silent.vbs"
    timeout /t 3 /nobreak >nul
) else (
    echo [OK] Web 服务已在运行
)

:: 检查端口 5000
echo [2/3] 检查 5000 端口...
netstat -ano | findstr ":5000" | findstr "LISTENING" >nul
if %errorlevel% neq 0 (
    echo [ERROR] 5000 端口未监听，Web 服务可能启动失败
    pause
    exit /b 1
)
echo [OK] 5000 端口正常

:: 启动 SSH 隧道（后台）
echo [3/3] 启动公网隧道...
echo [INFO] 正在连接 localhost.run，请稍等...
echo.

:: 用 PowerShell 后台启动 SSH，输出到日志
start "Tunnel" powershell -WindowStyle Hidden -Command "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -R 80:localhost:5000 nokey@localhost.run 2>&1 | ForEach-Object { $_ | Out-File -Append -FilePath '%~dp0logs\tunnel.log' -Encoding utf8 }"

timeout /t 6 /nobreak >nul

:: 尝试从日志提取 URL
powershell -NoProfile -Command "
    $log = Get-Content '%~dp0logs\tunnel.log' -ErrorAction SilentlyContinue -Raw
    if ($log -match '([a-z0-9]+\.lhr\.life)') {
        $url = 'https://' + $matches[1]
        Write-Host ''
        Write-Host '==========================================' -ForegroundColor Green
        Write-Host '    🎉 公网访问地址已生成！' -ForegroundColor Green
        Write-Host '==========================================' -ForegroundColor Green
        Write-Host ''
        Write-Host "    $url" -ForegroundColor Cyan
        Write-Host ''
        Write-Host '==========================================' -ForegroundColor Green
        start $url
    } else {
        Write-Host ''
        Write-Host '⏳ 隧道正在建立中...' -ForegroundColor Yellow
        Write-Host '   请等待 10 秒后查看 logs\tunnel.log' -ForegroundColor DarkGray
    }
"

echo.
echo [INFO] 按回车关闭此窗口（隧道会在后台继续运行）
pause >nul
