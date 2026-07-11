import { hasBackendSession } from './backendSession'
import {
  createAliExpressHotBroadcast,
  fetchAliExpressHotBroadcasts,
  markAliExpressHotBroadcastRead,
} from './aliexpressHotBroadcastApi'
import {
  appendHotBroadcast,
  loadHotBroadcasts as loadLocalHotBroadcasts,
  markBroadcastRead as markLocalBroadcastRead,
} from '@/utils/temuHotBroadcast'

export async function loadHotBroadcasts(auth = null, options = {}) {
  if (hasBackendSession(auth)) {
    return fetchAliExpressHotBroadcasts({ storeId: options.storeId })
  }
  return loadLocalHotBroadcasts()
}

export async function publishHotBroadcast(payload, auth = null) {
  if (hasBackendSession(auth)) {
    return createAliExpressHotBroadcast(payload)
  }
  const entry = {
    id: Date.now(),
    time: payload.time || new Date().toLocaleString('zh-CN', { hour12: false }),
    sku: payload.sku,
    name: payload.name,
    dailySales: payload.dailySales,
    avg7DayDaily: payload.avg7DayDaily,
    surgeRatio: payload.surgeRatio,
    operator: payload.operator || '系统',
    readBy: [],
    storeId: payload.storeId || '',
  }
  appendHotBroadcast(entry)
  return entry
}

export async function markHotBroadcastRead(broadcastId, readerName, auth = null, readerId = '') {
  if (hasBackendSession(auth)) {
    return markAliExpressHotBroadcastRead(broadcastId, {
      readerName,
      readerId,
    })
  }
  return markLocalBroadcastRead(broadcastId, readerName)
}

export async function bootstrapHotBroadcasts(products = [], auth = null, options = {}) {
  return loadHotBroadcasts(auth, options)
}

export { bootstrapHotBroadcasts as bootstrapAliExpressHotBroadcasts }
