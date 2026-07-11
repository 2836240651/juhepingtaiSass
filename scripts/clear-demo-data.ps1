# 清除 SQLite 与本地缓存中的 demo/mock 数据
# 用法: powershell -File scripts\clear-demo-data.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "==> purge demo/mock rows in crosshub.db" -ForegroundColor Cyan
Set-Location (Join-Path $Root "backend\python")
py clear_demo_data.py

Write-Host ""
Write-Host "完成。请刷新浏览器；若 Temu 仍显示旧数据，请硬刷新 (Ctrl+F5)。" -ForegroundColor Green
