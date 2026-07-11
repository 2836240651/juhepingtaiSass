param(
    [Parameter(Mandatory = $true)]
    [int]$TenantId,
    [string]$Date = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$PythonDir = Join-Path $Root "backend\python"

$args = @("crawl.py", "--tenant-id", $TenantId)
if ($Date) { $args += @("--date", $Date) }

Push-Location $PythonDir
try {
    py @args
} finally {
    Pop-Location
}
