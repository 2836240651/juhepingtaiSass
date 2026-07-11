import { hasBackendSession } from './backendSession'
import {
  createBackendHotBroadcast,
  fetchBackendHotBroadcasts,
  markBackendHotBroadcastRead,
} from './temuHotBroadcastApi'
import {
  appendHotBroadcast,
  loadHotBroadcasts as loadLocalHotBroadcasts,
  markBroadcastRead as markLocalBroadcastRead,
} from '@/utils/temuHotBroadcast'

export async function loadHotBroadcasts(auth = null) {
  if (hasBackendSession(auth)) {
    return fetchBackendHotBroadcasts()
  }
  return loadLocalHotBroadcasts()
}

export async function publishHotBroadcast(payload, auth = null) {
  if (hasBackendSession(auth)) {
    return createBackendHotBroadcast(payload)
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
    shopId: payload.shopId || '',
  }
  appendHotBroadcast(entry)
  return entry
}

export async function markHotBroadcastRead(broadcastId, readerName, auth = null, readerId = '') {
  if (hasBackendSession(auth)) {
    return markBackendHotBroadcastRead(broadcastId, {
      readerName,
      readerId,
    })
  }
  markLocalBroadcastRead(broadcastId, readerName)
}

export async function bootstrapHotBroadcasts(products = [], auth = null) {
  return loadHotBroadcasts(auth)
}
