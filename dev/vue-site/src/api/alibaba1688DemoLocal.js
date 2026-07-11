import { loadScoped, resolveTenantId, saveScoped } from '@/utils/tenantStorage'
import {
  ALIBABA1688_OPERATOR,
  PURCHASE_ORDERS_SEED,
  PURCHASE_ORDER_TEMPLATES,
  SUPPLIER_ALERTS_SEED,
  SUPPLIER_ALERT_TEMPLATES,
} from '@/constants/alibaba1688'

const STORAGE_KEY = 'crosshub_1688_demo'

function loadAll(tenantId = resolveTenantId()) {
  return loadScoped(tenantId, STORAGE_KEY, { purchaseOrders: [], supplierAlerts: [] })
    || { purchaseOrders: [], supplierAlerts: [] }
}

function saveAll(data, tenantId = resolveTenantId()) {
  saveScoped(tenantId, STORAGE_KEY, data)
}

function hashStoreId(id) {
  let hash = 0
  for (let i = 0; i < id.length; i += 1) {
    hash = (hash * 31 + id.charCodeAt(i)) >>> 0
  }
  return hash
}

function varyNumber(base, storeId, index, spread = 0.15) {
  const hash = hashStoreId(`${storeId}_${index}`)
  const ratio = 1 + ((hash % 100) / 100 - 0.5) * spread * 2
  return Math.max(0, Math.round(base * ratio))
}

function storeKey(storeId) {
  return String(storeId || '').replace(/[^a-zA-Z0-9]/g, '').slice(-6).toUpperCase() || '1688'
}

function generateOrdersForStore(store, startIndex = 0) {
  const prefix = storeKey(store.id)
  return PURCHASE_ORDER_TEMPLATES.map((item, index) => {
    const qty = varyNumber(item.quantity, store.id, index)
    const unitPrice = Number((item.unitPrice * (1 + ((hashStoreId(store.id + index) % 10) - 5) / 200)).toFixed(2))
    return {
      id: `po_${prefix}_${index + startIndex}`,
      storeId: store.id,
      orderNo: `CG${prefix}${String(index + 1).padStart(3, '0')}`,
      productName: item.productName,
      sku: item.sku,
      supplierName: item.supplierName,
      quantity: qty,
      unitPrice,
      amount: Number((qty * unitPrice).toFixed(2)),
      linkedPlatform: item.linkedPlatform,
      status: item.status,
      createdAt: '2026-06-24 09:00:00',
      payDeadline: item.status === 'pending_payment' ? '2026-06-24 18:00:00' : '',
      expectedShipAt: '2026-06-26',
      operator: ALIBABA1688_OPERATOR.name,
    }
  })
}

function generateAlertsForStore(store, startIndex = 0) {
  const prefix = storeKey(store.id)
  return SUPPLIER_ALERT_TEMPLATES.map((item, index) => ({
    id: `sa_${prefix}_${index + startIndex}`,
    storeId: store.id,
    type: item.type,
    supplierName: item.supplierName,
    productName: item.productName,
    sku: `SKU-${prefix}-${index + 1}`,
    detail: item.detail,
    severity: item.severity,
    reportedAt: '2026-06-24 10:00:00',
    resolved: false,
  }))
}

function seedDefaults(data) {
  const next = {
    purchaseOrders: [...data.purchaseOrders],
    supplierAlerts: [...data.supplierAlerts],
  }

  for (const order of PURCHASE_ORDERS_SEED) {
    if (!next.purchaseOrders.some((row) => row.id === order.id)) {
      next.purchaseOrders.push({ ...order })
    }
  }

  for (const alert of SUPPLIER_ALERTS_SEED) {
    if (!next.supplierAlerts.some((row) => row.id === alert.id)) {
      next.supplierAlerts.push({ ...alert })
    }
  }

  return next
}

export function ensureAlibaba1688DemoData(stores = []) {
  let data = seedDefaults(loadAll())
  const boundIds = new Set(stores.map((store) => store.id))

  data.purchaseOrders = data.purchaseOrders.filter((item) => boundIds.has(item.storeId))
  data.supplierAlerts = data.supplierAlerts.filter((item) => boundIds.has(item.storeId))

  for (const store of stores) {
    if (!data.purchaseOrders.some((item) => item.storeId === store.id)) {
      data.purchaseOrders.push(...generateOrdersForStore(store))
    }
    if (!data.supplierAlerts.some((item) => item.storeId === store.id)) {
      data.supplierAlerts.push(...generateAlertsForStore(store))
    }
  }

  saveAll(data)
  return data
}

export function loadAlibaba1688DemoData(stores = []) {
  const data = ensureAlibaba1688DemoData(stores)
  const boundIds = new Set(stores.map((store) => store.id))
  return {
    purchaseOrders: data.purchaseOrders.filter((item) => boundIds.has(item.storeId)),
    supplierAlerts: data.supplierAlerts.filter((item) => boundIds.has(item.storeId)),
  }
}

