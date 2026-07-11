import axios from 'axios'
import { AppApiError, getAppErrorMessage, toAppApiError } from '@/utils/appErrorCode'
import { service, getAccessToken } from './request'
import { mapReptileSaleToTemuProduct } from '@/utils/mapReptileSaleToTemuProduct'
import { enrichAllProducts } from '@/utils/temu'
import { applyServerAlgorithms } from '@/utils/temuServerAlgo'
import { hasBackendSession } from './backendSession'
import { scopeStores } from '@/utils/scope'
import { isTemuBackendEnabled, TEMU_API_BASE_URL } from './config'
import { fetchPlatformStores } from './platformAccounts'
import {
  fetchLocalTemuSalesTrend,
  fetchLocalTemuStores,
  loadLocalTemuOperationalData,
} from './temuDemoLocal'

const TEMU_PLATFORM = 'temu'

function isDemoShopId(id) {
  return /^(demo_|mock_)/i.test(String(id || ''))
}

export function canUseTemuBackend(auth) {
  return hasBackendSession(auth)
}

export async function fetchTemuSessionStatus() {
  const res = await service.get('/api/temu/session', { skipGlobalErrorToast: true })
  return res?.data ?? res ?? {}
}

export async function openTemuSellerLogin() {
  const res = await service.post('/api/temu/login/open', {}, { skipGlobalErrorToast: true })
  return res?.data ?? res ?? {}
}

export async function pollTemuSessionUntilReady({ timeoutMs = 300000, intervalMs = 3000 } = {}) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    const session = await fetchTemuSessionStatus()
    if (session.ready) return session
    if (session.profile_busy && session.logged_in && session.mall_id) return session
    await sleep(intervalMs)
  }
  throw new AppApiError('登录等待超时，请确认已在弹出窗口完成登录并选择店铺后重试', 'CRAWL_NOT_LOGGED_IN')
}

export async function pollTemuProfileIdle({ timeoutMs = 120000, intervalMs = 2000 } = {}) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    const session = await fetchTemuSessionStatus()
    if (!session.profile_busy) return session
    await sleep(intervalMs)
  }
  throw new AppApiError(
    '登录窗口仍占用浏览器，请关闭 CrossHub 弹出的登录浏览器后重试',
    'CRAWL_IN_PROGRESS',
  )
}

export async function fetchTemuStores(auth) {
  if (canUseTemuBackend(auth)) {
    const [shopsRes, boundRes] = await Promise.all([
      service.get('/api/temu/shops', { skipGlobalErrorToast: true }),
      fetchPlatformStores(TEMU_PLATFORM),
    ])
    const list = shopsRes?.data ?? []
    const shops = (Array.isArray(list) ? list : [])
      .filter((shop) => !isDemoShopId(shop.shop_id))
      .map((shop) => ({
      id: shop.shop_id,
      storeName: shop.bound_store_name || shop.shop_name || shop.shop_id,
      platform: TEMU_PLATFORM,
      isUpload: shop.is_upload,
      externalShopId: shop.external_shop_id || shop.shop_id,
      platformAccountId: shop.platform_account_id || '',
    }))
    const shopById = new Map(shops.map((shop) => [shop.id, shop]))
    const boundStores = (boundRes?.data || boundRes || []).map((store) => ({
      ...store,
      externalShopId: store.externalShopId || store.external_shop_id || '',
    }))
    const merged = []
    const seen = new Set()
    for (const store of boundStores) {
      const extId = store.externalShopId
      const shop = extId ? shopById.get(extId) : null
      const id = shop?.id || extId || store.id
      if (!id || seen.has(id)) continue
      seen.add(id)
      merged.push({
        id,
        storeName: store.storeName || shop?.storeName || id,
        platform: TEMU_PLATFORM,
        isUpload: shop?.isUpload,
        externalShopId: extId || id,
        accountId: store.id,
        needsShopLink: !extId,
      })
    }
    return scopeStores(merged, auth)
  }
  return fetchLocalTemuStores(auth)
}

export async function fetchTemuOperationalData({ shopId } = {}) {
  const params = {}
  if (shopId && shopId !== 'all') params.shop_id = shopId

  const res = await service.get('/api/temu/operational', { params })
  const products = (res.products || []).map((row) => mapReptileSaleToTemuProduct(row))
  const enriched = enrichAllProducts(products)
  const merged = applyServerAlgorithms(enriched, {
    loseProducts: res.lose_products || [],
    lowWarnings: res.low_warnings || [],
    inventoryWarnings: res.inventory_warnings || [],
    overloadProducts: res.overload_products || [],
  })

  return {
    products: merged,
    meta: {
      source: 'backend',
      reportTime: res.report_time,
      salesCount: products.length,
      loseCount: (res.lose_products || []).length,
      restockCount: (res.inventory_warnings || []).length,
      overloadCount: (res.overload_products || []).length,
    },
  }
}

export async function fetchTemuSalesTrend({ auth, shopId, days = 7 } = {}) {
  if (canUseTemuBackend(auth)) {
    const params = { days }
    if (shopId && shopId !== 'all') params.shop_id = shopId
    const res = await service.get('/api/temu/trend', { params })
    return {
      labels: res.labels || [],
      values: res.values || [],
    }
  }
  return fetchLocalTemuSalesTrend({ shopId, days })
}

export async function loadTemuModuleData({ auth, shopId }) {
  if (canUseTemuBackend(auth)) {
    return fetchTemuOperationalData({ shopId })
  }
  return loadLocalTemuOperationalData({ shopId })
}

const CRAWL_POLL_MS = 2000
const CRAWL_MAX_WAIT_MS = 300000

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export function formatCrawlError(errorCode, message) {
  return getAppErrorMessage(errorCode, message || '数据同步失败')
}

export async function triggerTemuCrawl(options = {}) {
  const body = {}
  if (options.reportTime) body.report_time = options.reportTime

  const token = getAccessToken()
  const res = await axios.post('/api/temu/crawl', body, {
    baseURL: import.meta.env.DEV ? '' : TEMU_API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    validateStatus: () => true,
    timeout: 120000,
  })

  const payload = res.data
  const job = payload?.data ?? payload
  if (res.status === 202 || payload?.code === 0) {
    return { conflict: false, job }
  }
  if (res.status === 409 || payload?.code === 409) {
    return {
      conflict: true,
      job,
      message: getAppErrorMessage(payload?.error_code, payload?.msg || '已有爬取任务进行中'),
    }
  }
  throw toAppApiError(payload, '触发爬取失败')
}

export async function fetchTemuCrawlJob(jobId) {
  const res = await service.get(`/api/temu/crawl/${jobId}`, { skipGlobalErrorToast: true })
  return res?.data ?? res
}

export async function refreshTemuDataWithCrawl(options = {}) {
  const started = await triggerTemuCrawl(options)
  const jobId = started.job?.job_id
  if (!jobId) {
    throw new AppApiError('未获取到爬取任务 ID', 'CRAWL_PROCESS_FAILED')
  }

  const deadline = Date.now() + CRAWL_MAX_WAIT_MS
  while (Date.now() < deadline) {
    const job = await fetchTemuCrawlJob(jobId)
    if (job.status === 'success') {
      return { success: true, job, conflict: started.conflict }
    }
    if (job.status === 'failed') {
      throw new AppApiError(
        formatCrawlError(job.error_code, job.error_message),
        job.error_code || 'CRAWL_PROCESS_FAILED',
      )
    }
    await sleep(CRAWL_POLL_MS)
  }
  throw new AppApiError(
    started.conflict ? '已有爬取任务进行中，等待超时，请稍后再试' : '数据同步超时，请稍后重试',
    started.conflict ? 'CRAWL_IN_PROGRESS' : 'CRAWL_TIMEOUT',
  )
}
