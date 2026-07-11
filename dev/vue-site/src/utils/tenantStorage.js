/**
 * 按租户隔离浏览器 localStorage 数据。
 */
import { isTemuBackendEnabled } from '@/api/config'

export const DEMO_TEMPLATE_TENANT_ID = 1

export function resolveTenantId(authOrId) {
  if (typeof authOrId === 'number' && authOrId > 0) return authOrId
  if (authOrId?.tenantId) return Number(authOrId.tenantId)
  if (authOrId?.tenant_id) return Number(authOrId.tenant_id)

  const backend = Number(localStorage.getItem('backend_tenant_id') || 0)
  if (backend > 0) return backend

  const local = Number(localStorage.getItem('crosshub_local_tenant_id') || 0)
  if (local > 0) return local

  return isTemuBackendEnabled() ? 0 : DEMO_TEMPLATE_TENANT_ID
}

/** 已关闭所有前端 Demo 模板数据注入 */
export function isDemoTemplateEnabled() {
  return false
}

export function scopedKey(tenantId, baseKey) {
  return `crosshub:t${tenantId}:${baseKey}`
}

export function loadScoped(tenantId, baseKey, fallback = null) {
  const key = scopedKey(tenantId, baseKey)
  try {
    const raw = localStorage.getItem(key)
    if (raw != null) return JSON.parse(raw)

    const legacy = localStorage.getItem(baseKey)
    if (legacy != null && isDemoTemplateEnabled(tenantId)) {
      localStorage.setItem(key, legacy)
      return JSON.parse(legacy)
    }
  } catch {
    return fallback
  }
  return fallback
}

export function saveScoped(tenantId, baseKey, data) {
  localStorage.setItem(scopedKey(tenantId, baseKey), JSON.stringify(data))
}

export function removeScoped(tenantId, baseKey) {
  localStorage.removeItem(scopedKey(tenantId, baseKey))
}

export function requireTenantId(authOrId) {
  const tenantId = resolveTenantId(authOrId)
  if (!tenantId) {
    throw new Error('缺少租户上下文')
  }
  return tenantId
}

export function setLocalTenantId(tenantId) {
  if (tenantId) {
    localStorage.setItem('crosshub_local_tenant_id', String(tenantId))
  } else {
    localStorage.removeItem('crosshub_local_tenant_id')
  }
}
