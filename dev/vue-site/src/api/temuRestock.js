import { hasBackendSession } from './backendSession'
import {
  fetchBackendTemuRestockStatusMap,
  restockStatusKey,
  upsertBackendTemuRestockStatus,
} from './temuRestockApi'
import {
  getTemuRestockStatus as getLocalTemuRestockStatus,
  getTemuRestockStatusMap as getLocalTemuRestockStatusMap,
  updateTemuRestockStatus as updateLocalTemuRestockStatus,
} from './temuRestockLocal'

export { restockStatusKey }

export function resolveTemuRestockStatus(restockStatusMap, product) {
  if (!restockStatusMap || !product?.sku) return null
  const scopedKey = restockStatusKey(product.storeId, product.sku)
  return restockStatusMap[scopedKey] || restockStatusMap[product.sku] || null
}

export async function loadTemuRestockStatusMap(auth = null) {
  if (hasBackendSession(auth)) {
    return fetchBackendTemuRestockStatusMap()
  }
  return getLocalTemuRestockStatusMap()
}

export function getTemuRestockStatus(sku, auth = null, shopId = '') {
  if (hasBackendSession(auth)) {
    return null
  }
  return getLocalTemuRestockStatus(sku)
}

export async function saveTemuRestockStatus(payload, auth = null) {
  const shopId = payload.shopId || ''
  const sku = payload.sku
  const status = payload.status || 'pending'
  const note = payload.note || ''

  if (hasBackendSession(auth)) {
    return upsertBackendTemuRestockStatus({ shopId, sku, status, note })
  }

  return updateLocalTemuRestockStatus(sku, { status, note })
}
