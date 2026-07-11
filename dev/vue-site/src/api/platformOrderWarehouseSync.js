import { PLATFORM_ORDER_STORAGE_KEYS } from '@/constants/platformShipRequests'
import { statusLabel } from '@/utils/warehouseOrders'
import { loadScoped, resolveTenantId, saveScoped } from '@/utils/tenantStorage'

const ALIBABA1688_STORAGE_KEY = 'crosshub_1688_demo'

function loadDomesticState(storageKey) {
  const tenantId = resolveTenantId()
  return loadScoped(tenantId, storageKey, { date: '', syncedAt: '', items: [] })
    || { date: '', syncedAt: '', items: [] }
}

function saveDomesticState(storageKey, state) {
  saveScoped(resolveTenantId(), storageKey, state)
}

function load1688State() {
  const tenantId = resolveTenantId()
  return loadScoped(tenantId, ALIBABA1688_STORAGE_KEY, { purchaseOrders: [], supplierAlerts: [] })
    || { purchaseOrders: [], supplierAlerts: [] }
}

function save1688State(data) {
  saveScoped(resolveTenantId(), ALIBABA1688_STORAGE_KEY, data)
}

export function updateDomesticPlatformOrder(platformKey, orderId, patch) {
  const storageKey = PLATFORM_ORDER_STORAGE_KEYS[platformKey]
  if (!storageKey) throw new Error('不支持的平台')

  const state = loadDomesticState(storageKey)
  const index = state.items.findIndex((item) => item.id === orderId)
  if (index === -1) throw new Error('平台订单不存在')

  state.items[index] = { ...state.items[index], ...patch }
  saveDomesticState(storageKey, state)
  return state.items[index]
}

export function update1688PlatformOrder(orderId, patch) {
  const data = load1688State()
  const index = data.purchaseOrders.findIndex((item) => item.id === orderId)
  if (index === -1) throw new Error('采购单不存在')

  data.purchaseOrders[index] = { ...data.purchaseOrders[index], ...patch }
  save1688State(data)
  return data.purchaseOrders[index]
}

export function buildWarehouseFeedbackPatch(warehouseOrder) {
  if (!warehouseOrder) return null
  return {
    warehouseOrderId: warehouseOrder.id,
    warehouseOrderNo: warehouseOrder.orderNo,
    warehouseId: warehouseOrder.warehouseId,
    warehouseName: warehouseOrder.warehouseName,
    warehouseStatus: warehouseOrder.status,
    warehouseStatusLabel: statusLabel(warehouseOrder.status),
    warehouseUpdatedAt: warehouseOrder.updatedAt,
  }
}

export function findDomesticPlatformOrder(platformKey, orderId) {
  const storageKey = PLATFORM_ORDER_STORAGE_KEYS[platformKey]
  if (!storageKey) return null
  const state = loadDomesticState(storageKey)
  return state.items.find((item) => item.id === orderId) || null
}

export function find1688PlatformOrder(orderId) {
  const data = load1688State()
  return data.purchaseOrders.find((item) => item.id === orderId) || null
}

export function syncPlatformOrderFromWarehouseOrder(warehouseOrder) {
  if (!warehouseOrder?.fromPlatformOrder) return null

  const { platformKey, platformOrderId } = warehouseOrder.fromPlatformOrder
  const patch = buildWarehouseFeedbackPatch(warehouseOrder)
  if (!patch) return null

  if (platformKey === '1688') {
    return update1688PlatformOrder(platformOrderId, patch)
  }

  const storageKey = PLATFORM_ORDER_STORAGE_KEYS[platformKey]
  if (!storageKey) return null

  const state = loadDomesticState(storageKey)
  const index = state.items.findIndex((item) => item.id === platformOrderId)
  if (index === -1) return null

  state.items[index] = { ...state.items[index], ...patch }
  saveDomesticState(storageKey, state)
  return state.items[index]
}
