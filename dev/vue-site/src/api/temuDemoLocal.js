import { TEMU_PRODUCTS_RAW } from '@/constants/temu'
import { fetchLocalPlatformStores } from './platformAccountsLocal'
import { enrichAllProducts } from '@/utils/temu'
import { scopeStores } from '@/utils/scope'

const TEMU_PLATFORM = 'temu'

function filterRawByShop(rawList, shopId) {
  if (!shopId || shopId === 'all') return rawList
  return rawList.filter((item) => item.storeId === shopId)
}

export function fetchLocalTemuStores(auth) {
  const res = fetchLocalPlatformStores(TEMU_PLATFORM)
  const stores = (res.data || []).map((store) => ({
    id: store.id,
    storeName: store.storeName,
    platform: TEMU_PLATFORM,
    isUpload: true,
  }))
  return scopeStores(stores, auth)
}

export function loadLocalTemuOperationalData() {
  return {
    products: [],
    meta: {
      source: 'empty',
      reportTime: '',
      salesCount: 0,
      loseCount: 0,
      restockCount: 0,
      overloadCount: 0,
    },
  }
}

export function fetchLocalTemuSalesTrend({ shopId, days = 7 } = {}) {
  const raw = filterRawByShop(TEMU_PRODUCTS_RAW, shopId)
  const labels = []
  const values = []

  for (let offset = days - 1; offset >= 0; offset -= 1) {
    const date = new Date()
    date.setDate(date.getDate() - offset)
    labels.push(`${date.getMonth() + 1}/${date.getDate()}`)
    const dayIndex = (days - 1) - offset
    const total = raw.reduce((sum, item) => sum + (item.salesLast7Days?.[dayIndex] ?? 0), 0)
    values.push(total)
  }

  return { labels, values }
}
