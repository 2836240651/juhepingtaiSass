import { useAuthStore } from '@/stores/auth'
import { hasBackendSession } from './backendSession'
import {
  cancelBackendWarehouseOrder,
  createBackendWarehouseOrder,
  deleteBackendWarehouseOrder,
  fetchBackendWarehouseOrder,
  fetchBackendWarehouseOrders,
  releaseBackendWarehouseOrder,
  reviewBackendWarehouseOrder,
  shipBackendWarehouseOrder,
} from './warehouseOrdersApi'
import {
  cancelLocalWarehouseOrder,
  createLocalWarehouseOrder,
  deleteLocalWarehouseOrder,
  fetchLocalWarehouseOrderById,
  fetchLocalWarehouseOrders,
  markLocalWarehouseOrderShipped,
  releaseLocalBlockedWarehouseOrder,
  submitLocalWarehouseReview,
  warehouseOrderStats,
} from './warehouseOrdersLocal'

export function canUseWarehouseBackend(auth) {
  return hasBackendSession(auth)
}

function resolveSubmitter(auth) {
  if (auth.isBoss) {
    return {
      id: auth.backendLinked ? String(auth.backendUserId || 'boss_admin') : 'boss_admin',
      name: auth.displayName || '企业管理员',
      role: 'boss',
    }
  }
  if (auth.isWarehouse) {
    return {
      id: auth.backendLinked ? String(auth.backendUserId || auth.warehouse.id) : auth.warehouse.id,
      name: auth.warehouse.name,
      role: 'warehouse',
    }
  }
  return {
    id: auth.backendLinked ? String(auth.backendUserId || auth.employee.id) : auth.employee.id,
    name: auth.employee.name,
    role: 'employee',
  }
}

function resolveReviewer(auth) {
  return {
    id: auth.backendLinked ? String(auth.backendUserId || auth.warehouse.id) : auth.warehouse.id,
    name: auth.warehouse.name,
  }
}

function resolveWarehouseScope(auth) {
  if (auth.isWarehouse) {
    if (auth.backendLinked && auth.warehouseScope?.length) {
      return auth.warehouseScope
    }
    return auth.warehouse?.warehouseIds || []
  }
  return null
}

function canAccessWarehouseOrder(auth, order) {
  if (!auth.isWarehouse || !order) return true
  const scope = resolveWarehouseScope(auth)
  if (!scope?.length) return false
  return scope.includes(order.warehouseId)
}

function resolveEmployeeFilter(auth) {
  if (!auth.isEmployee) return {}
  if (auth.backendLinked) {
    return { submittedById: String(auth.backendUserId || auth.employee.id) }
  }
  return { submittedById: auth.employee?.id }
}

export async function fetchWarehouseOrders(auth, filters = {}) {
  const employeeFilter = resolveEmployeeFilter(auth)
  const warehouseScope = resolveWarehouseScope(auth)

  if (canUseWarehouseBackend(auth)) {
    const data = await fetchBackendWarehouseOrders()
    let orders = data?.orders || []
    if (warehouseScope?.length) {
      const allowed = new Set(warehouseScope)
      orders = orders.filter((item) => allowed.has(item.warehouseId))
    }
    if (auth.isEmployee) {
      const ownerId = String(auth.backendUserId || auth.employee?.id || '')
      orders = orders.filter((item) => String(item.submittedById) === ownerId)
    }
    if (filters.status) {
      orders = orders.filter((item) => item.status === filters.status)
    }
    orders.sort((a, b) => String(b.submittedAt).localeCompare(String(a.submittedAt)))
    return { data: orders, stats: data?.stats || warehouseOrderStats(orders) }
  }

  const query = { ...filters, ...employeeFilter }
  if (warehouseScope) query.warehouseIds = warehouseScope
  const orders = fetchLocalWarehouseOrders(query)
  return { data: orders, stats: warehouseOrderStats(orders) }
}

export async function fetchWarehouseOrder(id, auth) {
  if (canUseWarehouseBackend(auth)) {
    return fetchBackendWarehouseOrder(id)
  }
  return fetchLocalWarehouseOrderById(id)
}

export async function createWarehouseOrder(auth, payload) {
  if (canUseWarehouseBackend(auth)) {
    return createBackendWarehouseOrder(payload)
  }
  return createLocalWarehouseOrder(payload, resolveSubmitter(auth))
}

export async function submitWarehouseReview(auth, orderId, payload) {
  if (canUseWarehouseBackend(auth)) {
    return reviewBackendWarehouseOrder(orderId, payload)
  }
  return submitLocalWarehouseReview(orderId, payload, resolveReviewer(auth))
}

export async function cancelWarehouseOrder(orderId, auth) {
  if (canUseWarehouseBackend(auth)) {
    return cancelBackendWarehouseOrder(orderId)
  }
  return cancelLocalWarehouseOrder(orderId)
}

export async function deleteWarehouseOrder(orderId, auth) {
  if (canUseWarehouseBackend(auth)) {
    return deleteBackendWarehouseOrder(orderId)
  }
  return deleteLocalWarehouseOrder(orderId)
}

export async function markWarehouseOrderShipped(orderId, auth) {
  if (canUseWarehouseBackend(auth)) {
    return shipBackendWarehouseOrder(orderId)
  }
  return markLocalWarehouseOrderShipped(orderId)
}

export async function releaseBlockedWarehouseOrder(auth, orderId, payload) {
  if (canUseWarehouseBackend(auth)) {
    return releaseBackendWarehouseOrder(orderId, payload)
  }
  return releaseLocalBlockedWarehouseOrder(orderId, payload, resolveReviewer(auth))
}

export function canManageOrder(auth, order) {
  if (!order) return false
  if (auth.isBoss || auth.isWarehouse) return true
  if (auth.isEmployee) {
    const ownerId = auth.backendLinked
      ? String(auth.backendUserId || auth.employee.id)
      : auth.employee.id
    return String(order.submittedById) === String(ownerId)
  }
  return false
}

export function canReviewOrder(auth, order) {
  if (!auth.isWarehouse || !order) return false
  if (!canAccessWarehouseOrder(auth, order)) return false
  return order.status === 'pending_review'
}

export function canCancelOrder(auth, order) {
  if (!canManageOrder(auth, order)) return false
  return ['pending_review', 'blocked'].includes(order.status)
}

export function canDeleteOrder(auth, order) {
  if (!auth.isBoss || !order) return false
  return true
}

export function canMarkShipped(auth, order) {
  if (!auth.isWarehouse || !order) return false
  if (!canAccessWarehouseOrder(auth, order)) return false
  return order.status === 'pending_shipment'
}

export function canReleaseBlocked(auth, order) {
  if (!auth.isWarehouse || !order) return false
  if (!canAccessWarehouseOrder(auth, order)) return false
  return order.status === 'blocked'
}

export function useWarehouseOrderAuth() {
  const auth = useAuthStore()
  return {
    auth,
    isBoss: auth.isBoss,
    isEmployee: auth.isEmployee,
    isWarehouse: auth.isWarehouse,
    canCreate: auth.isBoss || auth.isEmployee,
    canReview: auth.isWarehouse,
  }
}
