Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' 自动获取项目路径（VBS 所在目录）
projectPath = fso.GetParentFolderName(WScript.ScriptFullName)

' 自动检测 Python 路径（优先 pythonw.exe，无窗口）
pythonPath = ""
On Error Resume Next
pythonPath = shell.RegRead("HKEY_LOCAL_MACHINE\SOFTWARE\Python\PythonCore\3.12\InstallPath\")
If Err.Number <> 0 Then
    Err.Clear
    pythonPath = shell.RegRead("HKEY_CURRENT_USER\SOFTWARE\Python\PythonCore\3.12\InstallPath\")
End If
On Error GoTo 0

If pythonPath = "" Then
    ' 回退到常见路径
    pythonPath = "C:\Users\h2377\AppData\Local\Programs\Python\Python312\"
End If

pythonwPath = fso.BuildPath(pythonPath, "pythonw.exe")
If Not fso.FileExists(pythonwPath) Then
    ' 如果找不到 pythonw，回退到 python.exe
    pythonwPath = fso.BuildPath(pythonPath, "python.exe")
End If

' 如果还是找不到，尝试直接用 pythonw（依赖 PATH）
If Not fso.FileExists(pythonwPath) Then
    pythonwPath = "pythonw"
End If

' 先检查并释放 5000 端口（通过执行 PowerShell 命令）
killCmd = "powershell -WindowStyle Hidden -Command ""Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"""
shell.Run killCmd, 0, True

' 启动 Web 服务（独立进程，无窗口）
command = "cmd /c cd /d """ & projectPath & """ && set PYTHONUTF8=1 && set PYTHONIOENCODING=utf-8 && set MPLBACKEND=Agg && """ & pythonwPath & """ """ & projectPath & "\web_app.py""""
shell.Run command, 0, False

' 等待服务启动
WScript.Sleep 3000

' 打开浏览器
shell.Run "http://127.0.0.1:5000", 1, False
