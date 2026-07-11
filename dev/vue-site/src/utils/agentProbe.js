const DEFAULT_PORT = 18765

/**
 * 探测本机 Amazon 同步助手健康端口（默认 :18765）。
 * 助手窗口打开即应返回 true，不依赖 Java 心跳 TTL。
 */
export async function probeLocalAgent(port = DEFAULT_PORT, timeoutMs = 2500) {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    await fetch(`http://127.0.0.1:${port}/health`, {
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

export function getAgentProbePort() {
  return DEFAULT_PORT
}
