$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:MPLBACKEND = "Agg"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$logDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir "web_service.log"
$python = "C:\Users\h2377\AppData\Local\Programs\Python\Python312\python.exe"

"[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Web watchdog started." | Add-Content -Path $logFile -Encoding utf8

while ($true) {
    try {
        "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Starting web_app.py" | Add-Content -Path $logFile -Encoding utf8
        & cmd.exe /c "`"$python`" -u `".\web_app.py`" >> `"$logFile`" 2>&1"
        $exitCode = $LASTEXITCODE
        "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] web_app.py exited with code $exitCode. Restarting in 3 seconds." | Add-Content -Path $logFile -Encoding utf8
    }
    catch {
        "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Watchdog error: $_" | Add-Content -Path $logFile -Encoding utf8
    }
    Start-Sleep -Seconds 3
}
