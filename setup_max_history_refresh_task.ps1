param(
    [string]$TaskName = "QuantMaxHistoryRefresh",
    [string]$ProjectDir = "",
    [string]$PythonExe = "C:\Users\h2377\AppData\Local\Programs\Python\Python312\python.exe",
    [string]$StartTime = "17:45"
)

if ([string]::IsNullOrWhiteSpace($ProjectDir)) {
    $ProjectDir = $PSScriptRoot
}

$refreshScript = Join-Path $ProjectDir "scripts\refresh_max_history.py"
$logDir = Join-Path $ProjectDir "logs"
$logFile = Join-Path $logDir "max_history_refresh.log"

if (-not (Test-Path $refreshScript)) {
    throw "refresh_max_history.py not found: $refreshScript"
}
if (-not (Test-Path $PythonExe)) {
    throw "Python executable not found: $PythonExe"
}
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$command = @"
Set-Location '$ProjectDir'
'==== ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' max history refresh ====' | Out-File -FilePath '$logFile' -Append -Encoding utf8
& '$PythonExe' '$refreshScript' *>> '$logFile'
exit `$LASTEXITCODE
"@

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -Command `$ErrorActionPreference='Stop'; $command"
$trigger = New-ScheduledTaskTrigger -Daily -At $StartTime
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Refresh quant market data with maximum available history." `
    -Force

Write-Host "Registered scheduled task: $TaskName"
Write-Host "Daily start time: $StartTime"
Write-Host "Log file: $logFile"
