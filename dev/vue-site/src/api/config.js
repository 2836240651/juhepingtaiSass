/** 项目内 Temu 后端（Java API） */
export const TEMU_API_BASE_URL =
  import.meta.env.VITE_TEMU_API_URL || 'http://localhost:18080'

/** 默认走后端；仅当 VITE_USE_TEMU_BACKEND=false 时启用纯前端 Demo */
export function isTemuBackendEnabled() {
  const flag = import.meta.env.VITE_USE_TEMU_BACKEND
  if (flag === 'false' || flag === '0') return false
  return true
}
