import { loadScoped, resolveTenantId, saveScoped } from '@/utils/tenantStorage'
import {
  ALIEXPRESS_HOT_BROADCASTS,
  ALIEXPRESS_OPERATOR,
  ALIEXPRESS_PRODUCTS_SEED,
  ALIEXPRESS_PRODUCT_TEMPLATES,
} from '@/constants/aliexpressDemo'

const STORAGE_KEY = 'crosshub_aliexpress_demo'

function loadAll(tenantId = resolveTenantId()) {
  return loadScoped(tenantId, STORAGE_KEY, { products: [], broadcasts: [] })
    || { products: [], broadcasts: [] }
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

function varyNumber(base, storeId, index, spread = 0.2) {
  const hash = hashStoreId(`${storeId}_${index}`)
  const ratio = 1 + ((hash % 100) / 100 - 0.5) * spread * 2
  const value = base * ratio
  return Number.isInteger(base) ? Math.max(0, Math.round(value)) : Math.max(0, Number(value.toFixed(2)))
}

function varyArray(baseArray, storeId, index) {
  return baseArray.map((value, i) => varyNumber(value, storeId, index + i + 1, 0.15))
}

function storeKey(storeId) {
  return String(storeId || '').replace(/[^a-zA-Z0-9]/g, '').slice(-8).toUpperCase() || 'AE'
}

function generateProductsForStore(store) {
  const prefix = storeKey(store.id)
  return ALIEXPRESS_PRODUCT_TEMPLATES.map((item, index) => ({
    sku: `AE-${prefix}-${index + 1}`,
    storeId: store.id,
    name: item.name,
    category: item.category,
    sellingPrice: varyNumber(item.sellingPrice, store.id, index, 0.1),
    costPrice: varyNumber(item.costPrice, store.id, index + 10, 0.1),
    platformFeeRate: item.platformFeeRate,
    logisticsFee: varyNumber(item.logisticsFee, store.id, index + 20, 0.1),
    officialStock: varyNumber(item.officialStock, store.id, index + 30, 0.18),
    localStock: varyNumber(item.localStock, store.id, index + 40, 0.18),
    daysWithoutSale: varyNumber(item.daysWithoutSale, store.id, index + 50, 0.4),
    dailySales: varyNumber(item.dailySales, store.id, index + 60, 0.2),
    salesLast7Days: varyArray(item.salesLast7Days, store.id, index + 70),
    owner: ALIEXPRESS_OPERATOR.name,
  }))
}

function seedDefaults(data) {
  const next = {
    products: [...data.products],
    broadcasts: [...data.broadcasts],
  }

  for (const product of ALIEXPRESS_PRODUCTS_SEED) {
    if (!next.products.some((row) => row.sku === product.sku)) {
      next.products.push({ ...product })
    }
  }

  for (const broadcast of ALIEXPRESS_HOT_BROADCASTS) {
    if (!next.broadcasts.some((row) => row.id === broadcast.id)) {
      next.broadcasts.push({ ...broadcast })
    }
  }

  return next
}

/** 涓哄綋鍓嶅凡缁戝畾鐨?AliExpress 搴楅摵娉ㄥ叆 / 琛ラ綈 Demo 杩愯惀鏁版嵁 */
export function ensureAliexpressDemoData(stores = []) {
  let data = seedDefaults(loadAll())
  const boundIds = new Set(stores.map((store) => store.id))

  data.products = data.products.filter((item) => boundIds.has(item.storeId))
  data.broadcasts = data.broadcasts.filter((item) => {
    const product = data.products.find((row) => row.sku === item.sku)
    return product && boundIds.has(product.storeId)
  })

  for (const store of stores) {
    const hasProducts = data.products.some((item) => item.storeId === store.id)
    if (!hasProducts) {
      data.products.push(...generateProductsForStore(store))
    }
  }

  saveAll(data)
  return data
}

export function fetchAliexpressDemoData(stores = []) {
  const data = ensureAliexpressDemoData(stores)
  const boundIds = new Set(stores.map((store) => store.id))

  return {
    success: true,
    data: {
      products: data.products.filter((item) => boundIds.has(item.storeId)),
      broadcasts: data.broadcasts,
      operator: ALIEXPRESS_OPERATOR,
    },
  }
}

