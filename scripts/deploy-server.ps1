# 构建并部署 CrossHub 到远程（端口 18080/18081，不占用 34206）
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$env:NODE_HOME = if ($env:NODE_HOME) { $env:NODE_HOME } else { "D:\dev\env\tools\node" }
$env:PATH = "$env:NODE_HOME;$env:PATH"

Set-Location $Root
$scriptsDir = Join-Path $Root "scripts"
if (-not (Test-Path (Join-Path $scriptsDir "node_modules\ssh2"))) {
    Push-Location $scriptsDir
    npm install --silent
    Pop-Location
}

if (-not $env:CROSSHUB_SSH_HOST -or -not $env:CROSSHUB_SSH_PASSWORD) {
    Write-Error "Set CROSSHUB_SSH_HOST and CROSSHUB_SSH_PASSWORD before deploying."
}

node (Join-Path $Root "scripts\deploy-server.js")
