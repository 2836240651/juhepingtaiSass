const DEFAULT_PORT = 16851

/**
 * 从浏览器探测本机紫鸟 WebDriver 端口（:16851）是否已监听。
 * 不依赖同步助手心跳，运营运行紫鸟 bat 后即可在网页看到「已就绪」。
 */
export async function probeLocalZiniao(port = DEFAULT_PORT, timeoutMs = 2500) {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    await fetch(`http://127.0.0.1:${port}/`, {
      method: 'GET',
      mode: 'no-cors',
      signal: controller.signal,
    })
    return true
  } catch {
    return false
  } finally {
    window.clearTimeout(timer)
  }
}

export function getZiniaoProbePort() {
  return DEFAULT_PORT
}
