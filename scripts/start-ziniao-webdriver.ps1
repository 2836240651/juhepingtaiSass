# Start Ziniao WebDriver mode (local API :16851)
# Usage: powershell -File scripts\start-ziniao-webdriver.ps1
# Quit normal Ziniao (including tray icon) before running.
$ErrorActionPreference = "Stop"

$ZiniaoExe = if ($env:ZINIAO_CLIENT_PATH) { $env:ZINIAO_CLIENT_PATH } else { "C:\Program Files\ziniao\ziniao.exe" }
$Port = if ($env:ZINIAO_SOCKET_PORT) { $env:ZINIAO_SOCKET_PORT } else { 16851 }

if (-not (Test-Path $ZiniaoExe)) {
    throw "Ziniao client not found: $ZiniaoExe"
}

$listening = netstat -ano | Select-String "LISTENING" | Select-String ":$Port "
if ($listening) {
    Write-Host "Ziniao WebDriver already listening on port $Port." -ForegroundColor Yellow
    exit 0
}

Write-Host "==> Starting Ziniao WebDriver mode (port=$Port)" -ForegroundColor Cyan
Start-Process -FilePath $ZiniaoExe -ArgumentList "--run_type=web_driver", "--ipc_type=http", "--port=$Port"
Start-Sleep -Seconds 6

$listening = netstat -ano | Select-String "LISTENING" | Select-String ":$Port "
if (-not $listening) {
    throw "Port $Port is not listening. Enable WebDriver in Ziniao Boss settings and quit normal Ziniao first."
}

Write-Host "Ziniao WebDriver ready: http://127.0.0.1:$Port" -ForegroundColor Green
