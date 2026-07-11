import { TEMU_API_BASE_URL } from '@/api/config'

function escapeBatValue(value = '') {
  return String(value).replace(/"/g, '""')
}

function resolveLauncherRoot() {
  const configured = import.meta.env.VITE_AGENT_LAUNCHER_ROOT
  if (configured) return configured.replace(/\//g, '\\')
  return 'D:\\NIUBI\\SaaS-HZ_WEB_Demo'
}

function resolveJavaApiUrl() {
  return TEMU_API_BASE_URL.replace(/\/$/, '')
}

function downloadTextFile(filename, content) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export function buildZiniaoLauncherBat(projectRoot = resolveLauncherRoot()) {
  const root = escapeBatValue(projectRoot)
  return `@echo off
chcp 65001 >nul
title CrossHub 紫鸟启动助手
echo 正在启动紫鸟 WebDriver 模式（端口 16851）...
echo 请先完全退出普通紫鸟（含右下角托盘图标）。
echo.
set "ZINIAO_EXE=C:\\Program Files\\ziniao\\ziniao.exe"
if not exist "%ZINIAO_EXE%" (
  echo [错误] 未找到紫鸟: %ZINIAO_EXE%
  echo 请联系 IT 安装紫鸟客户端。
  pause
  exit /b 3
)
netstat -ano | findstr ":16851" | findstr "LISTENING" >nul
if not errorlevel 1 (
  echo 紫鸟 WebDriver 已在运行，无需重复启动。
  goto :done
)
start "" "%ZINIAO_EXE%" --run_type=web_driver --ipc_type=http --port=16851
echo 等待紫鸟启动...
timeout /t 8 /nobreak >nul
netstat -ano | findstr ":16851" | findstr "LISTENING" >nul
if errorlevel 1 (
  echo [错误] 端口 16851 未监听。请确认已退出普通紫鸟，且 Boss 已开通 WebDriver。
  pause
  exit /b 4
)
:done
echo.
echo 紫鸟 WebDriver 已就绪。请回到 CrossHub 页面点击「刷新状态」。
echo 然后下载并运行「Amazon 同步助手」完成步骤 2。
pause
`
}

export function buildAmazonAgentLauncherBat({
  agentToken,
  projectRoot = resolveLauncherRoot(),
  javaApiUrl = resolveJavaApiUrl(),
}) {
  const root = escapeBatValue(projectRoot)
  const token = escapeBatValue(agentToken)
  const apiUrl = escapeBatValue(javaApiUrl)
  return `@echo off
chcp 65001 >nul
title CrossHub Amazon 同步助手
echo CrossHub Amazon 同步助手已启动。
echo 请保持本窗口打开，关闭后 Amazon 将不再自动同步。
echo API 地址: ${apiUrl}
echo 健康检查: http://127.0.0.1:18765/health
echo.
set "AGENT_TOKEN=${token}"
set "JAVA_API_URL=${apiUrl}"
set "AGENT_HEALTH_PORT=18765"
set "PYTHONPATH=${root}\\backend\\python"
cd /d "${root}"
where py >nul 2>&1
if errorlevel 1 (
  echo [错误] 未找到 Python，请联系 IT 安装 Python 3 并勾选 Add to PATH。
  pause
  exit /b 4
)
if not exist "${root}\\backend\\python\\scripts\\run_agent.py" (
  echo [错误] 找不到同步助手脚本，请确认项目路径: ${root}
  pause
  exit /b 3
)
:agent_loop
py "${root}\\backend\\python\\scripts\\run_agent.py"
if errorlevel 1 (
  echo.
  echo [警告] 同步助手异常退出，5 秒后自动重试...
  timeout /t 5 /nobreak >nul
  goto agent_loop
)
echo.
echo 同步助手已停止。
pause
`
}

export function downloadZiniaoLauncher() {
  downloadTextFile('CrossHub-紫鸟启动助手.bat', buildZiniaoLauncherBat())
}

export function downloadAmazonAgentLauncher(setupData) {
  const token = setupData?.agent_token || setupData?.token
  if (!token) {
    throw new Error('未获取到同步助手凭证')
  }
  downloadTextFile('CrossHub-Amazon同步助手.bat', buildAmazonAgentLauncherBat({ agentToken: token }))
}

export function getLauncherRootHint() {
  return resolveLauncherRoot()
}
