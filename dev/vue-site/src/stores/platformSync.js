import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { runPlatformAutoSync } from '@/api/platformSync'

const SESSION_SYNC_KEY = 'crosshub_platform_sync_done'

export const usePlatformSyncStore = defineStore('platformSync', () => {
  const items = ref([])
  const running = ref(false)
  const expanded = ref(true)
  const lastFinishedAt = ref('')
  const lastError = ref('')

  const hasItems = computed(() => items.value.length > 0)
  const successCount = computed(() => items.value.filter((item) => item.status === 'success').length)
  const failedCount = computed(() => items.value.filter((item) => item.status === 'failed').length)
  const emptyCount = computed(() => items.value.filter((item) => item.status === 'empty').length)
  const syncingCount = computed(() => items.value.filter((item) => item.status === 'syncing').length)
  const summaryText = computed(() => {
    if (running.value) return '正在同步店铺数据...'
    if (!items.value.length) return '暂无绑定店铺'
    if (failedCount.value > 0) {
      return emptyCount.value > 0
        ? `${successCount.value} 成功 · ${failedCount.value} 失败 · ${emptyCount.value} 无数据`
        : `${successCount.value} 成功 · ${failedCount.value} 待处理`
    }
    if (emptyCount.value > 0) return `${successCount.value} 成功 · ${emptyCount.value} 无数据`
    return `${successCount.value} 个店铺已同步`
  })

  function updateItems(nextItems = []) {
    items.value = nextItems.map((item) => ({ ...item }))
  }

  function updateStoreStatus({
    platform,
    storeId = '',
    storeName = '',
    externalShopId = '',
    status,
    message = '',
    rowCount = 0,
    syncedAt = '',
  }) {
    const keyCandidates = new Set()
    if (platform && storeId) keyCandidates.add(`${platform}:${storeId}`)
    if (platform && externalShopId) keyCandidates.add(`${platform}:${externalShopId}`)

    let matched = false
    items.value = items.value.map((item) => {
      const keyHit = keyCandidates.has(item.key)
      const metaHit =
        item.platform === platform
        && (
          (storeId && (item.storeId === storeId || item.externalShopId === storeId))
          || (externalShopId && (item.externalShopId === externalShopId || item.storeId === externalShopId))
          || (storeName && item.storeName === storeName)
        )
      if (!keyHit && !metaHit) return item
      matched = true
      return {
        ...item,
        status,
        message,
        rowCount,
        syncedAt: syncedAt || item.syncedAt,
      }
    })

    if (!matched && platform && (storeId || storeName)) {
      items.value = [
        ...items.value,
        {
          key: `${platform}:${storeId || externalShopId || storeName}`,
          platform,
          storeId: storeId || externalShopId || storeName,
          storeName: storeName || storeId || externalShopId,
          externalShopId,
          platformLabel: platform,
          status,
          message,
          rowCount,
          syncedAt,
        },
      ]
    }
  }

  function shouldAutoSync(auth) {
    if (!auth?.backendLinked || auth.isWarehouse) return false
    if (sessionStorage.getItem(SESSION_SYNC_KEY) === '1') return false
    return true
  }

  async function runSync(auth, { force = false } = {}) {
    if (running.value) return
    if (!auth?.backendLinked || auth.isWarehouse) return

    running.value = true
    lastError.value = ''
    try {
      const result = await runPlatformAutoSync(auth, {
        onProgress: updateItems,
      })
      updateItems(result.items || [])
      lastFinishedAt.value = new Date().toLocaleString('zh-CN', { hour12: false })
      if (force) {
        sessionStorage.setItem(SESSION_SYNC_KEY, '1')
      }
    } catch (err) {
      lastError.value = err.message || '自动同步失败'
    } finally {
      running.value = false
    }
  }

  async function runAutoSyncOnLogin(auth) {
    if (!shouldAutoSync(auth)) return
    sessionStorage.setItem(SESSION_SYNC_KEY, '1')
    await runSync(auth)
  }

  async function retry(auth) {
    await runSync(auth, { force: true })
  }

  function resetSession() {
    sessionStorage.removeItem(SESSION_SYNC_KEY)
    items.value = []
    running.value = false
    lastFinishedAt.value = ''
    lastError.value = ''
  }

  return {
    items,
    running,
    expanded,
    lastFinishedAt,
    lastError,
    hasItems,
    successCount,
    failedCount,
    syncingCount,
    summaryText,
    updateStoreStatus,
    updateItems,
    runAutoSyncOnLogin,
    retry,
    resetSession,
    shouldAutoSync,
  }
})
