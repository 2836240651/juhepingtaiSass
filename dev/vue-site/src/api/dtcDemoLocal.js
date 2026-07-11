import { loadScoped, resolveTenantId, saveScoped } from '@/utils/tenantStorage'
import {
  DTC_CAMPAIGNS_SEED,
  DTC_CAMPAIGN_TEMPLATES,
  DTC_PRODUCTS_SEED,
  DTC_PRODUCT_TEMPLATES,
  DTC_STORE_META_SEED,
  DTC_TRAFFIC_TEMPLATE,
  DTC_TRAFFIC_WORDPRESS_TEMPLATE,
} from '@/constants/dtcDemo'

const STORAGE_KEY = 'crosshub_dtc_demo'

const EMPTY_DATA = () => ({
  products: [],
  campaigns: [],
  traffic: {},
  meta: {},
})

function loadAll(tenantId = resolveTenantId()) {
  const data = loadScoped(tenantId, STORAGE_KEY, null)
  return data ? { ...EMPTY_DATA(), ...data } : EMPTY_DATA()
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

function varyNumber(base, storeId, index, spread = 0.25) {
  const hash = hashStoreId(`${storeId}_${index}`)
  const ratio = 1 + ((hash % 100) / 100 - 0.5) * spread * 2
  const value = base * ratio
  return Number.isInteger(base) ? Math.max(0, Math.round(value)) : Math.max(0, Number(value.toFixed(2)))
}

function normalizePlatform(platform) {
  return String(platform || '').trim().toLowerCase()
}

function storeKey(storeId) {
  return String(storeId || '').replace(/[^a-zA-Z0-9]/g, '').slice(-8).toUpperCase() || 'STORE'
}

function inferDomain(store) {
  const account = String(store.account || '').trim()
  if (account.includes('@')) {
    const host = account.split('@')[1]
    return host ? `shop.${host}` : '—'
  }
  if (account.includes('.')) return account
  const slug = String(store.storeName || 'store')
    .replace(/\s+/g, '-')
    .replace(/[^\w-]/g, '')
    .toLowerCase()
  return slug ? `${slug}.example.com` : '—'
}

function inferCurrency(platform) {
  return normalizePlatform(platform) === 'shopify' ? 'USD' : '—'
}

function generateProductsForStore(store) {
  const platform = normalizePlatform(store.platform)
  const templates = DTC_PRODUCT_TEMPLATES[platform] || DTC_PRODUCT_TEMPLATES.shopify
  const prefix = storeKey(store.id)

  return templates.map((item, index) => ({
    sku: `DTC-${prefix}-${index + 1}`,
    storeId: store.id,
    name: item.name,
    category: item.category,
    price: varyNumber(item.price, store.id, index, 0.12),
    cost: varyNumber(item.cost, store.id, index + 10, 0.1),
    stock: varyNumber(item.stock, store.id, index + 20, 0.18),
    dailyOrders: varyNumber(item.dailyOrders, store.id, index + 30, 0.22),
    dailyViews: varyNumber(item.dailyViews, store.id, index + 40, 0.2),
    conversionRate: varyNumber(item.conversionRate, store.id, index + 50, 0.08),
    daysWithoutSale: varyNumber(item.daysWithoutSale, store.id, index + 60, 0.5),
  }))
}

function generateCampaignsForStore(store) {
  const platform = normalizePlatform(store.platform)
  const templates = DTC_CAMPAIGN_TEMPLATES[platform] || DTC_CAMPAIGN_TEMPLATES.shopify

  return templates.map((item, index) => ({
    id: `camp_${store.id}_${index + 1}`,
    storeId: store.id,
    name: item.name,
    status: item.status,
    budget: varyNumber(item.budget, store.id, index + 70, 0.15),
    spent: varyNumber(item.spent, store.id, index + 80, 0.15),
    orders: varyNumber(item.orders, store.id, index + 90, 0.2),
    roas: varyNumber(item.roas, store.id, index + 100, 0.1),
  }))
}

function generateTrafficForStore(store) {
  const platform = normalizePlatform(store.platform)
  const template =
    platform === 'wordpress' ? DTC_TRAFFIC_WORDPRESS_TEMPLATE : DTC_TRAFFIC_TEMPLATE

  return template.map((item, index) => ({
    source: item.source,
    visits: varyNumber(item.visits, store.id, index + 110, 0.18),
    orders: varyNumber(item.orders, store.id, index + 120, 0.2),
    conversion: varyNumber(item.conversion, store.id, index + 130, 0.08),
    spend: varyNumber(item.spend, store.id, index + 140, 0.15),
  }))
}

function generateMetaForStore(store) {
  return {
    domain: inferDomain(store),
    currency: inferCurrency(store.platform),
  }
}

function seedDefaults(data) {
  const next = {
    products: [...data.products],
    campaigns: [...data.campaigns],
    traffic: { ...data.traffic },
    meta: { ...data.meta },
  }

  for (const product of DTC_PRODUCTS_SEED) {
    if (!next.products.some((row) => row.sku === product.sku)) {
      next.products.push({ ...product })
    }
  }

  for (const campaign of DTC_CAMPAIGNS_SEED) {
    if (!next.campaigns.some((row) => row.id === campaign.id)) {
      next.campaigns.push({ ...campaign })
    }
  }

  for (const [storeId, meta] of Object.entries(DTC_STORE_META_SEED)) {
    if (!next.meta[storeId]) {
      next.meta[storeId] = { ...meta }
    }
  }

  for (const storeId of Object.keys(DTC_STORE_META_SEED)) {
    if (!next.traffic[storeId]) {
      const store = { id: storeId, platform: storeId.includes('wordpress') ? 'wordpress' : 'shopify' }
      next.traffic[storeId] = generateTrafficForStore(store)
    }
  }

  return next
}

/** 为当前已绑定的独立站店铺注入 / 补齐 Demo 运营数据 */
export function ensureDtcDemoData(stores = []) {
  let data = seedDefaults(loadAll())
  const boundIds = new Set(stores.map((store) => store.id))

  data.products = data.products.filter((item) => boundIds.has(item.storeId))
  data.campaigns = data.campaigns.filter((item) => boundIds.has(item.storeId))
  data.traffic = Object.fromEntries(
    Object.entries(data.traffic).filter(([storeId]) => boundIds.has(storeId)),
  )
  data.meta = Object.fromEntries(
    Object.entries(data.meta).filter(([storeId]) => boundIds.has(storeId)),
  )

  for (const store of stores) {
    const hasProducts = data.products.some((item) => item.storeId === store.id)
    if (!hasProducts) {
      data.products.push(...generateProductsForStore(store))
    }

    const hasCampaigns = data.campaigns.some((item) => item.storeId === store.id)
    if (!hasCampaigns) {
      data.campaigns.push(...generateCampaignsForStore(store))
    }

    if (!data.traffic[store.id]) {
      data.traffic[store.id] = generateTrafficForStore(store)
    }

    if (!data.meta[store.id]) {
      data.meta[store.id] = DTC_STORE_META_SEED[store.id]
        ? { ...DTC_STORE_META_SEED[store.id] }
        : generateMetaForStore(store)
    }
  }

  saveAll(data)
  return data
}

export function fetchDtcDemoData(stores = []) {
  const data = ensureDtcDemoData(stores)
  const boundIds = new Set(stores.map((store) => store.id))

  return {
    success: true,
    data: {
      products: data.products.filter((item) => boundIds.has(item.storeId)),
      campaigns: data.campaigns.filter((item) => boundIds.has(item.storeId)),
      traffic: Object.fromEntries(
        Object.entries(data.traffic).filter(([storeId]) => boundIds.has(storeId)),
      ),
      meta: Object.fromEntries(
        Object.entries(data.meta).filter(([storeId]) => boundIds.has(storeId)),
      ),
    },
  }
}

export function getDtcStoreMeta(storeId) {
  const data = loadAll()
  return data.meta[storeId] || null
}
