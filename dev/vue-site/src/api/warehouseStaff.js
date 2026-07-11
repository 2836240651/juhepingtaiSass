import { hasBackendSession } from './backendSession'
import { service } from './request'
import {
  deleteLocalWarehouseStaff,
  fetchLocalWarehouseStaff,
  saveLocalWarehouseStaff,
  toggleLocalWarehouseStaffStatus,
} from './warehouseStaffLocal'

function mapStaff(row) {
  if (!row) return row
  return {
    id: row.id,
    name: row.name,
    account: row.account,
    role: row.role,
    phone: row.phone || '',
    status: row.status !== false,
    boundAt: row.boundAt || row.bound_at || '',
    warehouseIds: row.warehouseIds || row.warehouse_ids || [],
    warehouseNames: row.warehouseNames || row.warehouse_names || [],
  }
}

function toStaffPayload(payload) {
  const body = {
    name: payload.name,
    account: payload.account,
    phone: payload.phone || '',
    role: payload.role,
    status: payload.status !== false,
    warehouse_ids: payload.warehouseIds || [],
  }
  if (payload.password) body.password = payload.password
  return body
}

export function canManageWarehouseStaff(auth) {
  return Boolean(auth?.isBoss)
}

export function canUseWarehouseStaffBackend(auth) {
  return hasBackendSession(auth) && auth.isBoss
}

async function fetchBackendWarehouseStaff() {
  const res = await service.get('/api/warehouse/members')
  const rows = res?.data || []
  return { success: true, data: rows.map(mapStaff) }
}

export async function fetchWarehouseStaff(auth) {
  if (canUseWarehouseStaffBackend(auth)) {
    return await fetchBackendWarehouseStaff()
  }
  return fetchLocalWarehouseStaff()
}

export async function saveWarehouseStaff(auth, payload) {
  if (!canManageWarehouseStaff(auth)) {
    throw new Error('仅企业管理员可管理仓库人员')
  }
  if (canUseWarehouseStaffBackend(auth)) {
    const body = toStaffPayload(payload)
    const res = payload.id
      ? await service.put(`/api/warehouse/members/${payload.id}`, body)
      : await service.post('/api/warehouse/members', body)
    return { success: true, data: mapStaff(res?.data) }
  }

  const result = saveLocalWarehouseStaff(payload)
  if (result.error) throw new Error(result.error)
  return result
}

export async function deleteWarehouseStaff(auth, id) {
  if (!canManageWarehouseStaff(auth)) {
    throw new Error('仅企业管理员可管理仓库人员')
  }
  if (canUseWarehouseStaffBackend(auth)) {
    await service.delete(`/api/warehouse/members/${id}`)
    return { success: true }
  }

  const result = deleteLocalWarehouseStaff(id)
  if (result.error) throw new Error(result.error)
  return result
}

export async function toggleWarehouseStaffStatus(auth, id, status) {
  if (!canManageWarehouseStaff(auth)) {
    throw new Error('仅企业管理员可管理仓库人员')
  }
  if (canUseWarehouseStaffBackend(auth)) {
    const res = await service.patch(`/api/warehouse/members/${id}/status`, { status })
    return { success: true, data: mapStaff(res?.data) }
  }

  const result = toggleLocalWarehouseStaffStatus(id, status)
  if (result.error) throw new Error(result.error)
  return result
}
