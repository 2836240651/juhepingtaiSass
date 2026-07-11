import { fetchAllPlatformStores } from './platformAccounts'
import {
  canUseTemuBackend,
  fetchTemuOperationalData,
  fetchTemuSessionStatus,
  fetchTemuStores,
  openTemuSellerLogin,
  pollTemuSessionUntilReady,
  pollTemuProfileIdle,
  refreshTemuDataWithCrawl,
} from './temuApi'
import {
  canUseAliExpressBackend,
  refreshAliExpressDataWithCrawl,
  fetchTodayAliExpressOrdersFromApi,
} from './aliexpressApi'
import {
  canUseAmazonBackend,
  fetchAmazonDailyFromBackend,
  fetchAmazonInsightsFromBackend,
  refreshAmazonDailyWithSync,
  refreshAmazonReportsWithSync,
} from './amazonApi'
import { fetchAmazonIntegrationStatus } from './agentApi'
import { probeLocalZiniao } from '@/utils/ziniaoProbe'
import { probeLocalAgent } from '@/utils/agentProbe'
import { fetchAmazonStores } from './platformAccounts'
import { scopeStores } from '@/utils/scope'
import {
  DOMESTIC_PLATFORM_OPTIONS,
  DTC_PLATFORM_OPTIONS,
  MARKETPLACE_PLATFORM_OPTIONS,
} from '@/constants/platforms'

const BACKEND_AUTO_SYNC_PLATFORMS = new Set(['temu', 'aliexpress', 'amazon'])
const DEMO_AUTO_SYNC_PLATFORMS = new Set([])

const PLATFORM_LABELS = Object.fromEntries(
  [...MARKETPLACE_PLATFORM_OPTIONS, ...DOMESTIC_PLATFORM_OPTIONS, ...DTC_PLATFORM_OPTIONS].map(
    (item) => [item.value, item.label],
  ),
)

function platformLabel(platform) {
  return PLATFORM_LABELS[platform] || platform
}

function createSyncItem(store) {
  return {
    key: `${store.platform}:${store.id}`,
    platform: store.platform,
    storeId: store.id,
    storeName: store.storeName,
    externalShopId: store.externalShopId || '',
    platformLabel: platformLabel(store.platform),
    status: 'pending',
    message: '',
    syncedAt: '',
    rowCount: 0,
  }
}

export async function buildPlatformSyncTargets(auth) {
  const res = await fetchAllPlatformStores()
  return scopeStores(res.data || [], auth).map(createSyncItem)
}

function markItems(items, predicate, patch) {
  for (const item of items) {
    if (predicate(item)) {
      Object.assign(item, patch)
    }
  }
}

function resolveTemuShopId(target, temuShops = []) {
  return temuShops.find(
    (shop) =>
      shop.accountId === target.storeId
      || shop.id === target.storeId
      || (target.externalShopId && shop.externalShopId === target.externalShopId)
      || (target.externalShopId && shop.id === target.externalShopId)
      || shop.id === target.externalShopId
      || shop.storeName === target.storeName,
  )?.id
}

function applyTemuCrawlSuccess(temuTargets, temuShops, job = {}) {
  const rowsCount = Number(job.rows_count ?? job.rowsCount ?? 0)
  const reportTime = job.report_time || job.reportTime || ''
  if (rowsCount <= 0) return false

  let applied = false
  for (const target of temuTargets) {
    const shopId = resolveTemuShopId(target, temuShops)
    if (!shopId) {
      target.status = 'failed'
      target.message = '店铺尚未关联 Temu Shop ID，请到 Temu 运营页刷新后重试'
      continue
    }
    target.status = 'success'
    target.rowCount = rowsCount
    target.syncedAt = reportTime
    target.message = `已同步 ${rowsCount} 条销售数据`
    applied = true
  }
  return applied
}

async function verifyTemuShopTargets(temuTargets, temuShops, reportTime, job = {}) {
  if (applyTemuCrawlSuccess(temuTargets, temuShops, job)) {
    return
  }

  for (const target of temuTargets) {
    if (target.status === 'success') continue

    const shopId = resolveTemuShopId(target, temuShops)
    if (!shopId) {
      target.status = 'failed'
      target.message = '店铺尚未关联 Temu Shop ID，请到 Temu 运营页刷新后重试'
      continue
    }

    try {
      const data = await fetchTemuOperationalData({ shopId })
      const count = data.products?.length ?? 0
      target.rowCount = count
      target.syncedAt = data.meta?.reportTime || reportTime || ''
      if (count > 0) {
        target.status = 'success'
        target.message = `已同步 ${count} 条 SKU`
      } else {
        target.status = 'empty'
        target.message = '爬取完成，但未读取到当日销量数据'
      }
    } catch (err) {
      target.status = 'failed'
      target.message = err.message || '读取店铺数据失败'
    }
  }
}

async function syncTemuStores(auth, items, onProgress) {
  const temuTargets = items.filter((item) => item.platform === 'temu')
  if (!temuTargets.length) return

  if (!canUseTemuBackend(auth)) {
    markItems(items, (item) => item.platform === 'temu', {
      status: 'skipped',
      message: '未启用后端模式，无法自动爬取',
    })
    onProgress?.([...items])
    return
  }

  markItems(items, (item) => item.platform === 'temu', {
    status: 'syncing',
    message: '正在检查 Temu 登录状态...',
  })
  onProgress?.([...items])

  try {
    let session = await fetchTemuSessionStatus()
    if (!session.ready) {
      if (!session.profile_busy) {
        try {
          await openTemuSellerLogin()
        } catch {
          // best effort
        }
      }
      markItems(items, (item) => item.platform === 'temu', {
        status: 'syncing',
        message: '等待 Temu 卖家后台登录...',
      })
      onProgress?.([...items])
      try {
        session = await pollTemuSessionUntilReady({ timeoutMs: 300000, intervalMs: 3000 })
      } catch {
        markItems(items, (item) => item.platform === 'temu', {
          status: 'skipped',
          message: '尚未完成 Temu 登录，请到 Temu 运营页刷新数据',
        })
        onProgress?.([...items])
        return
      }
    }

    try {
      await pollTemuProfileIdle({ timeoutMs: 120000, intervalMs: 2000 })
    } catch {
      markItems(items, (item) => item.platform === 'temu', {
        status: 'skipped',
        message: '登录窗口仍占用浏览器，请关闭后重试',
      })
      onProgress?.([...items])
      return
    }

    markItems(items, (item) => item.platform === 'temu', {
      status: 'syncing',
      message: '正在同步 Temu 销售数据...',
    })
    onProgress?.([...items])

    const result = await refreshTemuDataWithCrawl()
    const reportTime = result.job?.report_time || ''
    const temuShops = await fetchTemuStores(auth)
    await verifyTemuShopTargets(temuTargets, temuShops, reportTime, result.job || {})
  } catch (err) {
    markItems(items, (item) => item.platform === 'temu', {
      status: 'failed',
      message: err.message || 'Temu 自动同步失败',
    })
  }

  onProgress?.([...items])
}

async function syncAliExpressStores(auth, items, onProgress) {
  const targets = items.filter((item) => item.platform === 'aliexpress')
  if (!targets.length) return

  if (!canUseAliExpressBackend(auth)) {
    markItems(items, (item) => item.platform === 'aliexpress', {
      status: 'skipped',
      message: '未启用后端模式，无法自动爬取',
    })
    onProgress?.([...items])
    return
  }

  markItems(items, (item) => item.platform === 'aliexpress', {
    status: 'syncing',
    message: '无头浏览器爬取订单...',
  })
  onProgress?.([...items])

  try {
    await refreshAliExpressDataWithCrawl()
    const orderRes = await fetchTodayAliExpressOrdersFromApi()
    const orders = orderRes.orders || []
    const syncedAt = orderRes.syncedAt || ''

    for (const target of targets) {
      const count = orders.filter((order) => order.storeId === target.storeId).length
      target.syncedAt = syncedAt
      if (count > 0) {
        target.status = 'success'
        target.rowCount = count
        target.message = `已同步 ${count} 笔今日订单`
      } else {
        target.status = 'empty'
        target.message = '店铺已绑定，但今日暂无订单'
      }
    }
  } catch (err) {
    markItems(items, (item) => item.platform === 'aliexpress', {
      status: 'failed',
      message: err.message || 'AliExpress 订单同步失败',
    })
  }

  onProgress?.([...items])
}

async function syncAmazonStores(auth, items, onProgress) {
  const targets = items.filter((item) => item.platform === 'amazon')
  if (!targets.length) return

  if (!canUseAmazonBackend()) {
    markItems(items, (item) => item.platform === 'amazon', {
      status: 'skipped',
      message: '未启用后端模式，无法自动同步',
    })
    onProgress?.([...items])
    return
  }

  let integration = {}
  let ziniaoReady = false
  let agentReady = false
  try {
    const [statusRes, localZiniao, localAgent] = await Promise.all([
      fetchAmazonIntegrationStatus(),
      probeLocalZiniao(),
      probeLocalAgent(),
    ])
    integration = statusRes.data || {}
    ziniaoReady = localZiniao || Boolean(integration.ziniao_online)
    agentReady = localAgent || Boolean(integration.agent_online)
  } catch {
    integration = {}
  }

  if (!agentReady) {
    markItems(items, (item) => item.platform === 'amazon', {
      status: 'failed',
      message: 'Amazon 同步助手未运行，请到「设置 → Amazon 同步助手」下载并启动',
    })
    onProgress?.([...items])
    return
  }

  if (!ziniaoReady) {
    markItems(items, (item) => item.platform === 'amazon', {
      status: 'failed',
      message: '紫鸟 WebDriver 未就绪，请到「设置 → Amazon 同步助手」下载紫鸟启动助手',
    })
    onProgress?.([...items])
    return
  }

  markItems(items, (item) => item.platform === 'amazon', {
    status: 'syncing',
    message: '紫鸟 Agent 同步 daily 数据...',
  })
  onProgress?.([...items])

  try {
    const stores = scopeStores((await fetchAmazonStores()).data || [], auth)
    const started = await refreshAmazonDailyWithSync(stores, { scope: 'daily' })
    let daily = started.data || (await fetchAmazonDailyFromBackend(stores)).data
    let reportsStarted = null
    if (started.partial || started.errorCode === 'AMAZON_NO_PRODUCT_ROWS') {
      reportsStarted = await refreshAmazonReportsWithSync(stores)
      const insights = reportsStarted.data || (await fetchAmazonInsightsFromBackend(stores)).data
      if (insights?.products?.length) {
        daily = { ...daily, syncedAt: insights.syncedAt || daily.syncedAt }
      }
    }
    const syncedAt = daily.syncedAt || ''
    for (const target of targets) {
      const metrics = (daily.accountMetrics || []).filter((m) => m.storeId === target.storeId)
      const reviews = (daily.reviews || []).filter((r) => r.storeId === target.storeId)
      const coupons = (daily.coupons || []).filter((c) => c.storeId === target.storeId)
      const shipments = (daily.shipments || []).filter((s) => s.storeId === target.storeId)
      const rowCount = metrics.length + reviews.length + coupons.length + shipments.length
      target.syncedAt = syncedAt
      target.rowCount = rowCount
      if (rowCount > 0) {
        target.status = 'success'
        target.message = `已同步 ${metrics.length} 指标 / ${reviews.length} 差评 / ${coupons.length} 优惠券 / ${shipments.length} 货件`
      } else if (started.partial || reportsStarted?.partial) {
        target.status = 'empty'
        target.message = started.warning || reportsStarted?.warning || '同步完成，但产品数据为空'
      } else {
        target.status = 'empty'
        target.message = started.message || '同步完成，暂无运营待办数据'
      }
    }
  } catch (err) {
    markItems(items, (item) => item.platform === 'amazon', {
      status: 'failed',
      message: err.message || 'Amazon 自动同步失败',
    })
  }

  onProgress?.([...items])
}

export async function runPlatformAutoSync(auth, { onProgress } = {}) {
  const items = await buildPlatformSyncTargets(auth)
  if (!items.length) {
    return { items: [], skipped: true, reason: 'no_stores' }
  }

  markItems(
    items,
    (item) => !BACKEND_AUTO_SYNC_PLATFORMS.has(item.platform) && !DEMO_AUTO_SYNC_PLATFORMS.has(item.platform),
    {
      status: 'skipped',
      message: '该平台暂未接入自动同步',
    },
  )
  onProgress?.([...items])

  const hasTemuTargets = items.some((item) => item.platform === 'temu')
  if (hasTemuTargets) {
    await syncTemuStores(auth, items, onProgress)
  }

  const hasAliExpressTargets = items.some((item) => item.platform === 'aliexpress')
  if (hasAliExpressTargets) {
    await syncAliExpressStores(auth, items, onProgress)
  }

  const hasAmazonTargets = items.some((item) => item.platform === 'amazon')
  if (hasAmazonTargets) {
    await syncAmazonStores(auth, items, onProgress)
  }

  return { items, skipped: false }
}
