import { loadScoped, resolveTenantId, saveScoped } from '@/utils/tenantStorage'
import {
  buildDemoSnapshotsForCompetitor,
  DEMO_COMPETITOR_IDS,
} from '@/constants/temuCompetitors'
import { localDateKey } from '@/utils/date'

const STORAGE_KEY = 'crosshub_temu_competitor_snapshots'
const MAX_DAYS = 30

function loadAll(tenantId = resolveTenantId()) {
  return loadScoped(tenantId, STORAGE_KEY, []) || []
}

function saveAll(data, tenantId = resolveTenantId()) {
  saveScoped(tenantId, STORAGE_KEY, data)
}

function todayKey() {
  return localDateKey()
}

/** 鎵归噺鏇挎崲鏌愮珵搴楃殑鍏ㄩ儴蹇収 */
export function replaceCompetitorSnapshots(competitorId, snapshots) {
  const others = loadAll().filter((item) => item.competitorId !== competitorId)
  const merged = [
    ...others,
    ...snapshots
      .filter((item) => item.competitorId === competitorId)
      .sort((a, b) => b.date.localeCompare(a.date))
      .slice(0, MAX_DAYS),
  ]
  saveAll(merged)
}

/** 涓哄崟涓珵搴楅噸寤?Demo 蹇収锛堢粦瀹氬埌璇ョ珵搴?id锛?*/
export function resetCompetitorSnapshots(competitor) {
  const snapshots = buildDemoSnapshotsForCompetitor(competitor).map((item) => ({
    ...item,
    demoVersion: 'v1',
  }))
  replaceCompetitorSnapshots(competitor.id, snapshots)
  return snapshots
}

/** 纭繚鎵€鏈?Demo 绔炲簵 id 鐨勫揩鐓у瓨鍦?*/
export function ensureDemoSnapshots() {
  for (const competitorId of DEMO_COMPETITOR_IDS) {
    if (getLatestSnapshot(competitorId)) continue
    const snapshots = buildDemoSnapshotsForCompetitor({ id: competitorId, url: '' })
    replaceCompetitorSnapshots(competitorId, snapshots.map((s) => ({ ...s, demoVersion: 'v1' })))
  }
}

/** @deprecated 浣跨敤 resetCompetitorSnapshots */
export function resetDemoSnapshots() {
  for (const competitorId of DEMO_COMPETITOR_IDS) {
    resetCompetitorSnapshots({ id: competitorId, url: '' })
  }
}

export function getCompetitorSnapshots(competitorId) {
  return loadAll()
    .filter((item) => item.competitorId === competitorId)
    .sort((a, b) => b.date.localeCompare(a.date))
}

export function getLatestSnapshot(competitorId) {
  const list = getCompetitorSnapshots(competitorId)
  return list[0] || null
}

export function getSnapshotByDate(competitorId, date) {
  return loadAll().find(
    (item) => item.competitorId === competitorId && item.date === date,
  ) || null
}

export function saveSnapshot(snapshot) {
  const existing = getCompetitorSnapshots(snapshot.competitorId).filter(
    (item) => item.date !== snapshot.date,
  )
  replaceCompetitorSnapshots(snapshot.competitorId, [...existing, snapshot])
  return snapshot
}

export function deleteCompetitorSnapshots(competitorId) {
  saveAll(loadAll().filter((item) => item.competitorId !== competitorId))
}

export function canCrawlToday(competitorId) {
  return !getSnapshotByDate(competitorId, todayKey())
}

export { todayKey }

