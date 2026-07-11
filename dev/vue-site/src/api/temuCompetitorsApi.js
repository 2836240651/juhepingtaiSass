import { service } from './request'
import { mapMonitorReport } from '@/utils/temuMonitorReport'

function unwrap(res) {
  return res?.data ?? res
}

function isActiveStatus(status) {
  return status === 'pending' || status === 'running'
}

function isTerminalStatus(status) {
  return status === 'success' || status === 'failed'
}

function parseHost(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url || ''
  }
}

function mapTarget(item) {
  return {
    id: item.id,
    label: item.label,
    url: item.target_url,
    host: item.host || parseHost(item.target_url),
    status: item.status,
    freshnessMinutes: item.freshness_minutes,
    latestSnapshotId: item.latest_snapshot_id || null,
    latestSnapshotAt: item.latest_snapshot_at || null,
    lastAnalyzedAt: item.latest_snapshot_at || null,
  }
}

async function fetchMonitorLatest(id) {
  const res = await service.get(`/api/monitor/targets/${id}/latest`)
  return unwrap(res) || {}
}

async function fetchMonitorHistory(id) {
  const res = await service.get(`/api/monitor/targets/${id}/history`)
  return unwrap(res) || { snapshots: [], jobs: [] }
}

async function fetchMonitorJob(jobId) {
  const res = await service.get(`/api/monitor/jobs/${jobId}`)
  return unwrap(res) || {}
}

async function triggerMonitorTarget(id, options = {}) {
  const normalized = typeof options === 'string' ? { reason: options } : options
  const res = await service.post(`/api/monitor/targets/${id}/trigger`, {
    reason: normalized.reason || 'manual refresh',
    force: !!normalized.force,
  })
  return unwrap(res) || {}
}

async function downloadMonitorTargetReportXlsx(id) {
  return service.get(`/api/monitor/targets/${id}/report.xlsx`, {
    responseType: 'blob',
  })
}

function wait(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

async function waitForJob(jobId, maxAttempts = 6, delayMs = 1000) {
  let lastJob = null
  for (let i = 0; i < maxAttempts; i += 1) {
    lastJob = await fetchMonitorJob(jobId)
    if (isTerminalStatus(lastJob.status)) {
      return lastJob
    }
    await wait(delayMs)
  }
  return lastJob
}

async function waitForActiveJob(targetId, latest = {}, maxAttempts = 6, delayMs = 1000) {
  if (!isActiveStatus(latest.latest_job_status || latest.latestJobStatus)) {
    return null
  }
  const history = await fetchMonitorHistory(targetId)
  const activeJobId = history.jobs?.[0]?.jobId || history.jobs?.[0]?.job_id
  if (!activeJobId) {
    return null
  }
  return waitForJob(activeJobId, maxAttempts, delayMs)
}

const MANUAL_CRAWL_POLL_ATTEMPTS = 30
const MANUAL_CRAWL_POLL_DELAY_MS = 2000

async function enqueueManualCrawl(target) {
  const latest = await fetchMonitorLatest(target.id)
  const latestJobStatus = latest.latest_job_status || latest.latestJobStatus

  if (isActiveStatus(latestJobStatus)) {
    await waitForActiveJob(
      target.id,
      latest,
      MANUAL_CRAWL_POLL_ATTEMPTS,
      MANUAL_CRAWL_POLL_DELAY_MS,
    )
    return
  }

  try {
    const job = await triggerMonitorTarget(target.id, {
      reason: 'manual refresh (force)',
      force: true,
    })
    if (job?.job_id) {
      await waitForJob(job.job_id, MANUAL_CRAWL_POLL_ATTEMPTS, MANUAL_CRAWL_POLL_DELAY_MS)
    }
  } catch (error) {
    if (error?.errorCode === 'MONITOR_JOB_IN_PROGRESS' && error?.data?.job_id) {
      await waitForJob(
        error.data.job_id,
        MANUAL_CRAWL_POLL_ATTEMPTS,
        MANUAL_CRAWL_POLL_DELAY_MS,
      )
      return
    }
    if (error?.errorCode !== 'MONITOR_JOB_IN_PROGRESS') {
      throw error
    }
  }
}

async function buildReportForTarget(target) {
  const [latest, history] = await Promise.all([
    fetchMonitorLatest(target.id),
    fetchMonitorHistory(target.id),
  ])
  return mapMonitorReport(target, latest, history)
}

export async function fetchBackendCompetitors() {
  const res = await service.get('/api/monitor/targets', {
    params: { platform: 'temu' },
  })
  return { success: true, data: (unwrap(res) || []).map(mapTarget) }
}

export async function saveBackendCompetitor(payload) {
  const body = {
    platform: 'temu',
    target_type: 'shop',
    label: payload.label,
    target_url: payload.url,
    freshness_minutes: 1440,
    crawl_strategy: 'store_listing',
    status: 'active',
  }
  const res = payload.id
    ? await service.put(`/api/monitor/targets/${payload.id}`, body)
    : await service.post('/api/monitor/targets', body)
  return { success: true, data: mapTarget(unwrap(res)) }
}

export async function deleteBackendCompetitor(id) {
  const res = await service.delete(`/api/monitor/targets/${id}`)
  return { success: true, data: unwrap(res) }
}

export async function fetchBackendCompetitorReports() {
  const competitorsRes = await fetchBackendCompetitors()
  const competitors = competitorsRes.data || []
  const reports = await Promise.all(competitors.map((item) => buildReportForTarget(item)))
  return { success: true, data: reports, competitors }
}

export async function discoverBackendCompetitors(payload = {}) {
  const res = await service.post('/api/temu/competitors/discover', {
    keyword: payload.keyword || 'fishing tackle',
    region: payload.region || 'za',
    limit: payload.limit || 10,
  })
  return { success: true, data: unwrap(res) || {} }
}

export async function analyzeBackendCompetitors(competitors = []) {
  const selectedIds = new Set((competitors || []).map((item) => item.id).filter(Boolean))
  const competitorsRes = await fetchBackendCompetitors()
  const allCompetitors = competitorsRes.data || []
  const targets = selectedIds.size
    ? allCompetitors.filter((item) => selectedIds.has(item.id))
    : allCompetitors

  for (const target of targets) {
    await enqueueManualCrawl(target)
  }

  const reports = await Promise.all(targets.map((item) => buildReportForTarget(item)))
  return {
    success: true,
    data: reports,
    competitors: allCompetitors,
  }
}

export async function downloadBackendCompetitorReport(report) {
  const blob = await downloadMonitorTargetReportXlsx(report.id)
  const objectUrl = window.URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = `${report.label || 'monitor-report'}-${report.crawlDate || 'latest'}.xlsx`
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  window.URL.revokeObjectURL(objectUrl)
}
