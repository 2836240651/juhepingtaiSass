import { hasBackendSession } from './backendSession'
import { service } from './request'
import {
  deleteLocalWarehouseSite,
  fetchLocalWarehouseSites,
  saveLocalWarehouseSite,
  toggleLocalWarehouseSiteStatus,
} from './warehouseSitesLocal'

function mapSite(row) {
  if (!row) return row
  return {
    id: row.id,
    name: row.name,
    code: row.code,
    address: row.address || '',
    status: row.status !== false,
    sortOrder: row.sortOrder ?? row.sort_order ?? 0,
    createdAt: row.createdAt || row.created_at || '',
  }
}

function toSitePayload(payload) {
  return {
    name: payload.name,
    code: payload.code,
    address: payload.address || '',
    status: payload.status !== false,
    sort_order: payload.sortOrder ?? 0,
  }
}

export function canUseWarehouseSitesBackend(auth) {
  return hasBackendSession(auth) && auth.isBoss
}

export async function fetchWarehouseSites(auth, { activeOnly = false } = {}) {
  if (canUseWarehouseSitesBackend(auth)) {
    const res = await service.get('/api/warehouse/sites', {
      params: { activeOnly },
    })
    return { success: true, data: (res?.data || []).map(mapSite) }
  }
  return fetchLocalWarehouseSites({ activeOnly })
}

export async function saveWarehouseSite(auth, payload) {
  if (canUseWarehouseSitesBackend(auth)) {
    const body = toSitePayload(payload)
    const res = payload.id
      ? await service.put(`/api/warehouse/sites/${payload.id}`, body)
      : await service.post('/api/warehouse/sites', body)
    return { success: true, data: mapSite(res?.data) }
  }

  const result = saveLocalWarehouseSite(payload)
  if (result.error) throw new Error(result.error)
  return result
}

export async function deleteWarehouseSite(auth, id) {
  if (canUseWarehouseSitesBackend(auth)) {
    await service.delete(`/api/warehouse/sites/${id}`)
    return { success: true }
  }

  const result = deleteLocalWarehouseSite(id)
  if (result.error) throw new Error(result.error)
  return result
}

export async function toggleWarehouseSiteStatus(auth, id, status) {
  if (canUseWarehouseSitesBackend(auth)) {
    const res = await service.patch(`/api/warehouse/sites/${id}/status`, { status })
    return { success: true, data: mapSite(res?.data) }
  }

  const result = toggleLocalWarehouseSiteStatus(id, status)
  if (result.error) throw new Error(result.error)
  return result
}
