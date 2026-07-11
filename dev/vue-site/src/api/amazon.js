import { hasBackendSession } from './backendSession'
import {
  fetchAmazonDailyData,
  markBuyerMessageReplied,
  markCaseRead,
  markReviewHandled,
  syncAmazonDailyData,
} from './amazonDailyLocal'
import {
  acknowledgeAmazonCaseBackend,
  fetchAmazonDailyFromBackend,
  fetchAmazonInsightsFromBackend,
  handleAmazonReviewBackend,
  refreshAmazonDailyWithSync,
  refreshAmazonInsightsWithSync,
  refreshAmazonReportsWithSync,
  refreshAmazonAllWithSync,
  replyAmazonMessageBackend,
  shipAmazonOutboundBackend,
} from './amazonApi'

import {
  fetchAmazonBossData,
  markOutboundShipped,
  syncAmazonBossData,
} from './amazonBossLocal'

function useAmazonBackend() {
  return hasBackendSession()
}

export async function loadAmazonBossInsights(stores) {
  if (useAmazonBackend()) {
    return fetchAmazonInsightsFromBackend(stores)
  }
  return fetchAmazonBossData(stores)
}

export async function refreshAmazonBossInsights(stores, options = {}) {
  if (useAmazonBackend()) {
    if (options.scope === 'reports') {
      return refreshAmazonReportsWithSync(stores, options)
    }
    return refreshAmazonInsightsWithSync(stores, options)
  }
  return syncAmazonBossData(stores, options)
}

export async function shipOutboundOrder(id, payload) {
  if (useAmazonBackend()) {
    return shipAmazonOutboundBackend(id, payload)
  }
  return markOutboundShipped(id, payload)
}

export async function loadAmazonDailyWorkflow(stores) {
  if (useAmazonBackend()) {
    return fetchAmazonDailyFromBackend(stores)
  }
  return fetchAmazonDailyData(stores)
}

export async function refreshAmazonDailyWorkflow(stores, options = {}) {
  if (useAmazonBackend()) {
    return refreshAmazonDailyWithSync(stores, options)
  }
  return syncAmazonDailyData(stores, options)
}

export async function refreshAmazonAccountHealth(stores, options = {}) {
  if (useAmazonBackend()) {
    return refreshAmazonDailyWithSync(stores, { ...options, scope: 'account_health' })
  }
  return syncAmazonDailyData(stores, options)
}

export async function refreshAmazonAllData(stores, options = {}) {
  if (useAmazonBackend()) {
    return refreshAmazonAllWithSync(stores, options)
  }
  return syncAmazonBossData(stores, options)
}

export async function replyBuyerMessage(id, payload) {
  if (useAmazonBackend()) {
    return replyAmazonMessageBackend(id, payload)
  }
  return markBuyerMessageReplied(id, payload)
}

export async function handleReview(id, payload) {
  if (useAmazonBackend()) {
    return handleAmazonReviewBackend(id, payload)
  }
  return markReviewHandled(id, payload)
}

export async function acknowledgeCase(id) {
  if (useAmazonBackend()) {
    return acknowledgeAmazonCaseBackend(id)
  }
  return markCaseRead(id)
}

/** @deprecated */
export function loadAmazonOperationalData(stores) {
  return loadAmazonDailyWorkflow(stores)
}
