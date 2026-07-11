import { service } from './request'

export async function fetchBackendWarehouseOrders() {
  const res = await service.get('/api/warehouse/orders', { skipGlobalErrorToast: true })
  return res?.data ?? res
}

export async function fetchBackendWarehouseOrder(id) {
  const res = await service.get(`/api/warehouse/orders/${id}`, { skipGlobalErrorToast: true })
  return res?.data ?? res
}

export async function createBackendWarehouseOrder(payload) {
  const res = await service.post('/api/warehouse/orders', payload)
  return res?.data ?? res
}

export async function reviewBackendWarehouseOrder(id, payload) {
  const res = await service.post(`/api/warehouse/orders/${id}/review`, payload)
  return res?.data ?? res
}

export async function releaseBackendWarehouseOrder(id, payload) {
  const res = await service.post(`/api/warehouse/orders/${id}/release`, payload)
  return res?.data ?? res
}

export async function shipBackendWarehouseOrder(id) {
  const res = await service.post(`/api/warehouse/orders/${id}/ship`)
  return res?.data ?? res
}

export async function cancelBackendWarehouseOrder(id) {
  const res = await service.post(`/api/warehouse/orders/${id}/cancel`)
  return res?.data ?? res
}

export async function deleteBackendWarehouseOrder(id) {
  const res = await service.delete(`/api/warehouse/orders/${id}`)
  return res?.data ?? res
}

export async function createBackendWarehouseOrderFromPlatform(payload) {
  const res = await service.post('/api/warehouse/orders/from-platform', payload)
  return res?.data ?? res
}
