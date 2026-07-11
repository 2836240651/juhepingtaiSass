import { hasBackendSession } from './backendSession'
import { service } from './request'

export function canUseTenantFeaturesBackend(auth) {
  return hasBackendSession(auth) && Boolean(auth?.isBoss)
}

export async function fetchTenantFeatures(auth) {
  if (!canUseTenantFeaturesBackend(auth)) {
    return { success: false, data: [] }
  }
  const res = await service.get('/api/tenant/features')
  return { success: true, data: res?.data || [] }
}

export async function updateTenantFeatures(auth, features) {
  if (!canUseTenantFeaturesBackend(auth)) {
    throw new Error('当前环境无法保存功能开关')
  }
  const res = await service.put('/api/tenant/features', { features })
  return res
}
