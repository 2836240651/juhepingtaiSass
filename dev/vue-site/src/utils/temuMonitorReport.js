import { resolveAppError } from './appErrorCode.js'

function pickNumber(...values) {
  for (const value of values) {
    if (value === null || value === undefined || value === '') continue
    const numeric = Number(value)
    if (!Number.isNaN(numeric)) return numeric
  }
  return 0
}

function pickText(...values) {
  for (const value of values) {
    if (typeof value === 'string' && value.trim()) return value
  }
  return ''
}

function formatPriceText(value) {
  const numeric = Number(value || 0)
  if (Number.isNaN(numeric) || numeric <= 0) return '--'
  return `¥${numeric.toFixed(2)}`
}

function formatListedLabel(value) {
  if (!value) return '--'
  return String(value).slice(0, 10)
}

function mapProductRow(item = {}) {
  const listedAt = pickText(item.listed_at, item.listedAt)
  return {
    productId: pickText(item.product_id, item.productId),
    name: pickText(item.product_name, item.productName),
    category: pickText(item.category),
    price: pickNumber(item.price),
    priceText: formatPriceText(item.price),
    dailySales: pickNumber(item.daily_sales, item.dailySales),
    totalSales: pickNumber(item.total_sales, item.totalSales),
    listedAt,
    listedLabel: formatListedLabel(listedAt),
    url: pickText(item.url),
    signalValue: pickText(item.signal_value, item.signalValue),
  }
}

function mapSalesOutlierRow(item = {}) {
  const row = mapProductRow(item)
  return {
    ...row,
    anomalyType: '销量异常',
    severity: pickNumber(item.daily_sales, item.dailySales) >= 50 ? 'high' : 'medium',
    prevDailySales: '--',
    avg7DailySales: '--',
    growthVsPrevText: row.signalValue || '--',
    growthVsAvgText: row.signalValue || '--',
  }
}

export function mapMonitorReport(target, latest = {}, history = { snapshots: [], jobs: [] }) {
  const snapshots = (history.snapshots || []).map((item) => ({
    snapshot_id: item.snapshot_id || item.snapshotId || '',
    snapshot_at: item.snapshot_at || item.snapshotAt || '',
    product_count: pickNumber(item.product_count, item.productCount),
    new_launch_count: pickNumber(item.new_launch_count, item.newLaunchCount),
    sales_outlier_count: pickNumber(item.sales_outlier_count, item.salesOutlierCount),
  }))
  const jobs = (history.jobs || []).map((item) => ({
    job_id: item.job_id || item.jobId || '',
    trigger_type: item.trigger_type || item.triggerType || '',
    status: item.status || '',
    queued_at: item.queued_at || item.queuedAt || '',
    finished_at: item.finished_at || item.finishedAt || '',
    error_code: item.error_code || item.errorCode || '',
    error_message: item.error_message || item.errorMessage || '',
    reason: item.reason || '',
  }))
  const summary = latest.summary || {}
  const artifacts = latest.artifacts || {}
  const latestJob = jobs[0] || {}
  const latestJobError = latestJob.error_code
    ? resolveAppError({ errorCode: latestJob.error_code, message: latestJob.error_message }, null)
    : null
  const recentLaunches = latest.recent_launches || latest.recentLaunches || []
  const salesOutliers = latest.sales_outliers || latest.salesOutliers || []
  return {
    id: target.id,
    label: target.label,
    url: target.url,
    host: target.host,
    analyzedAt: target.lastAnalyzedAt,
    crawlDate: (latest.latest_snapshot_at || latest.latestSnapshotAt)?.slice(0, 10) || null,
    previousCrawlDate: snapshots[1]?.snapshot_at?.slice(0, 10) || null,
    snapshotCount: snapshots.length,
    hasFreshData: !!(latest.has_fresh_data ?? latest.hasFreshData),
    latestJobStatus: latest.latest_job_status || latest.latestJobStatus || latestJob.status || null,
    latestJobId: latestJob.job_id || null,
    latestJobFinishedAt: latestJob.finished_at || null,
    latestJobErrorCode: latestJob.error_code || '',
    latestJobErrorMessage: latestJob.error_message || '',
    latestJobError,
    canTriggerNow: !!(latest.can_trigger_now ?? latest.canTriggerNow),
    reason: latest.reason || latestJob.reason || '',
    artifacts: {
      report_md_path: pickText(artifacts.report_md_path, artifacts.reportMdPath),
      report_xlsx_path: pickText(artifacts.report_xlsx_path, artifacts.reportXlsxPath),
    },
    history: {
      snapshots,
      jobs,
    },
    summary: {
      totalProducts: pickNumber(summary.product_count, summary.productCount),
      newToday: pickNumber(summary.new_launch_count, summary.newLaunchCount),
      recentListings: pickNumber(summary.new_launch_count, summary.newLaunchCount),
      salesSpikes: pickNumber(summary.sales_outlier_count, summary.salesOutlierCount),
      highSeveritySpikes: pickNumber(summary.sales_outlier_count, summary.salesOutlierCount),
    },
    newProducts: recentLaunches.map(mapProductRow),
    recentListings: recentLaunches.map(mapProductRow),
    salesSpikes: salesOutliers.map(mapSalesOutlierRow),
  }
}
