$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:MPLBACKEND = "Agg"
$env:PORT = if ($env:PORT) { $env:PORT } else { "5001" }

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$logDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir "public_server.log"

Write-Host "Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host "Opening Windows Firewall port $env:PORT..."
netsh advfirewall firewall add rule name="AI Quant Web $env:PORT" dir=in action=allow protocol=TCP localport=$env:PORT | Out-Null

Write-Host "Stopping existing Python listeners on port $env:PORT..."
$connections = Get-NetTCPConnection -LocalPort ([int]$env:PORT) -State Listen -ErrorAction SilentlyContinue
foreach ($connection in $connections) {
    Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
}

Write-Host "Starting public web server at http://0.0.0.0:$env:PORT ..."
Write-Host "Public URL: http://114.132.56.9:$env:PORT/"
cmd.exe /c "python -m waitress --host=0.0.0.0 --port=$env:PORT web_app:app 2>&1" | Tee-Object -FilePath $logFile -Append
