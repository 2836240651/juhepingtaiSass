# CrossHub Agent launcher (token injected by downloaded .bat)
param(
    [string]$AgentToken = $env:AGENT_TOKEN,
    [string]$JavaApiUrl = $env:JAVA_API_URL
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $Root "backend\python"

if ($AgentToken) {
    $env:AGENT_TOKEN = $AgentToken
}
if ($JavaApiUrl) {
    $env:JAVA_API_URL = $JavaApiUrl
}

if (-not $env:AGENT_TOKEN) {
    Write-Host "Missing AGENT_TOKEN. Download Amazon sync helper from CrossHub settings page." -ForegroundColor Red
    exit 2
}

Set-Location $Root
$agentScript = Join-Path $Root "backend\python\scripts\run_agent.py"
if (-not (Test-Path $agentScript)) {
    Write-Host "Agent script not found: $agentScript" -ForegroundColor Red
    exit 3
}

$py = Get-Command py -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "Python launcher 'py' not found. Install Python 3 and retry." -ForegroundColor Red
    exit 4
}

& py $agentScript
