import { isTemuBackendEnabled } from './config'
import { getAccessToken } from './request'

export function isBackendLinked() {
  return isTemuBackendEnabled() && Boolean(getAccessToken()) && localStorage.getItem('backend_linked') === '1'
}

/** 已登录且 Java API 会话有效（非纯前端 Demo） */
export function hasBackendSession(auth) {
  if (!isBackendLinked()) return false
  if (auth == null) return true
  return Boolean(auth.backendLinked)
}
