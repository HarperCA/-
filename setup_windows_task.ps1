param(
    [string]$TaskName = "QuantWebApp",
    [string]$ProjectDir = "C:\Users\h2377\Desktop\量化",
    [string]$PythonExe = "C:\Users\h2377\AppData\Local\Programs\Python\Python312\python.exe",
    [string]$StartTime = "08:55"
)

$script = Join-Path $ProjectDir "web_app.py"
if (-not (Test-Path $script)) {
    throw "web_app.py not found in $ProjectDir"
}

$action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$script`"" -WorkingDirectory $ProjectDir
$trigger = New-ScheduledTaskTrigger -Daily -At $StartTime
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 2)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Start the quant web app so APScheduler automations can run." -Force
Write-Host "Registered scheduled task: $TaskName"
