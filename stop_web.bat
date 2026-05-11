@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command "$currentPid = $PID; Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $currentPid -and ($_.CommandLine -like '*web_app.py*' -or $_.CommandLine -like '*run_web.ps1*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }; Write-Host 'Web service stopped.'"
