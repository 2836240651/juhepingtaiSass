import { loadScoped, resolveTenantId, saveScoped } from '@/utils/tenantStorage'
import { TEMU_RESTOCK_STATUS_SEED } from '@/constants/temuOps'

const STORAGE_KEY = 'crosshub_temu_restock_status'

function loadAll(tenantId = resolveTenantId()) {
  return loadScoped(tenantId, STORAGE_KEY, {}) || {}
}

function saveAll(data, tenantId = resolveTenantId()) {
  saveScoped(tenantId, STORAGE_KEY, data)
}

export function getTemuRestockStatusMap() {
  const stored = loadAll()
  return { ...TEMU_RESTOCK_STATUS_SEED, ...stored }
}

export function getTemuRestockStatus(sku) {
  return getTemuRestockStatusMap()[sku] || null
}

export function updateTemuRestockStatus(sku, payload) {
  const current = loadAll()
  current[sku] = { ...current[sku], ...payload }
  saveAll(current)
  return current[sku]
}

