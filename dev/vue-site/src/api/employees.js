import { isTemuBackendEnabled } from './config'
import { service } from './request'
import {
  deleteLocalEmployee,
  fetchLocalEmployees,
  saveLocalEmployee,
  toggleLocalEmployeeStatus,
} from './employeesLocal'

function mapMember(row) {
  if (!row) return row
  return {
    id: row.id,
    name: row.name,
    account: row.account,
    role: row.role,
    phone: row.phone || '',
    platforms: row.platforms || [],
    assignedStoreIds: row.assignedStoreIds || row.shop_ids || [],
    menuCodes: row.menu_codes || [],
    status: row.status !== false,
    boundAt: row.boundAt || row.bound_at || '',
  }
}

function toMemberPayload(payload) {
  const body = {
    name: payload.name,
    account: payload.account,
    phone: payload.phone || '',
    role: payload.role,
    platforms: payload.platforms || [],
    shop_ids: payload.assignedStoreIds || [],
    menu_codes: Array.isArray(payload.menuCodes) ? payload.menuCodes : [],
    status: payload.status !== false,
  }
  if (payload.password) body.password = payload.password
  return body
}

async function fetchBackendMembers() {
  const res = await service.get('/api/tenant/members')
  const rows = res?.data || []
  return { success: true, data: rows.map(mapMember) }
}

export async function fetchAssignableMenus() {
  if (!isTemuBackendEnabled()) return { success: true, data: [] }
  try {
    const res = await service.get('/api/tenant/assignable-menus')
    return { success: true, data: res?.data || [] }
  } catch {
    return { success: true, data: [] }
  }
}

export async function fetchEmployees() {
  if (isTemuBackendEnabled()) {
    try {
      return await fetchBackendMembers()
    } catch {
      /* fallback */
    }
  }
  return fetchLocalEmployees()
}

export async function saveEmployee(payload) {
  if (isTemuBackendEnabled()) {
    try {
      const body = toMemberPayload(payload)
      const res = payload.id
        ? await service.put(`/api/tenant/members/${payload.id}`, body)
        : await service.post('/api/tenant/members', body)
      return { success: true, data: mapMember(res?.data) }
    } catch (err) {
      throw err
    }
  }

  const result = saveLocalEmployee(payload)
  if (result.error) throw new Error(result.error)
  return result
}

export async function updateMemberScopes(memberId, { platforms, assignedStoreIds, menuCodes }) {
  const res = await service.put(`/api/tenant/members/${memberId}/scopes`, {
    platforms: platforms || [],
    shop_ids: assignedStoreIds || [],
    menu_codes: Array.isArray(menuCodes) ? menuCodes : [],
  })
  return { success: true, data: mapMember(res?.data) }
}

export async function deleteEmployee(id) {
  if (isTemuBackendEnabled()) {
    try {
      await service.delete(`/api/tenant/members/${id}`)
      return { success: true }
    } catch (err) {
      throw err
    }
  }

  const result = deleteLocalEmployee(id)
  if (result.error) throw new Error(result.error)
  return result
}

export async function toggleEmployeeStatus(id, status) {
  if (isTemuBackendEnabled()) {
    try {
      const res = await service.patch(`/api/tenant/members/${id}/status`, { status })
      return { success: true, data: mapMember(res?.data) }
    } catch (err) {
      throw err
    }
  }

  const result = toggleLocalEmployeeStatus(id, status)
  if (result.error) throw new Error(result.error)
  return result
}
