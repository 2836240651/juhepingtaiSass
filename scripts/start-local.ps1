# 本地启动：Java(18080) + Express(3000) + Vue(5173)
# 用法: powershell -File scripts\start-local.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

$env:NODE_HOME = if ($env:NODE_HOME) { $env:NODE_HOME } else { "D:\dev\env\tools\node" }
$env:PATH = "$env:NODE_HOME;$env:PATH"

function Stop-Port([int]$Port) {
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object {
            $p = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
            if ($p) {
                Write-Host "  stop port $Port : $($p.ProcessName) (PID $($p.Id))" -ForegroundColor Yellow
                Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
            }
        }
}

Write-Host "==> stop old listeners on 5173 / 18080 / 3000" -ForegroundColor Cyan
@(5173, 18080, 3000) | ForEach-Object { Stop-Port $_ }
Start-Sleep -Seconds 1

Write-Host "==> start Java API :18080" -ForegroundColor Cyan
$javaLauncher = Join-Path $env:TEMP "crosshub-java.ps1"
@(
    ". '$Root\scripts\env-java.ps1'"
    "Set-Location '$Root\backend\java'"
    "`$env:SPRING_PROFILES_ACTIVE='dev'"
    "mvn -q spring-boot:run"
) | Set-Content -Path $javaLauncher -Encoding UTF8
Start-Process powershell -WindowStyle Normal -ArgumentList @("-NoExit", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $javaLauncher)

Write-Host "==> start Express :3000" -ForegroundColor Cyan
$expressLauncher = Join-Path $env:TEMP "crosshub-express.ps1"
@(
    "Set-Location '$Root\script\api-server'"
    "if (-not (Test-Path node_modules)) { npm install }"
    "`$env:PORT='3000'"
    "npm start"
) | Set-Content -Path $expressLauncher -Encoding UTF8
Start-Process powershell -WindowStyle Normal -ArgumentList @("-NoExit", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $expressLauncher)

Write-Host "==> start Vue dev :5173" -ForegroundColor Cyan
$webLauncher = Join-Path $env:TEMP "crosshub-web.ps1"
@(
    "Set-Location '$Root\dev\vue-site'"
    "if (-not (Test-Path node_modules)) { npm install }"
    "npm run dev"
) | Set-Content -Path $webLauncher -Encoding UTF8
Start-Process powershell -WindowStyle Normal -ArgumentList @("-NoExit", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $webLauncher)

Start-Sleep -Seconds 8
Write-Host ""
Write-Host "Local URLs:" -ForegroundColor Green
Write-Host "  Web     http://localhost:5173"
Write-Host "  Java    http://localhost:18080/api/temu/shops"
Write-Host "  Express http://localhost:3000/api/health"
