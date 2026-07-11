import assert from 'node:assert/strict'
import { mapMonitorReport } from '../src/utils/temuMonitorReport.js'

const report = mapMonitorReport(
  {
    id: 'mt_synthetic',
    label: 'Synthetic Store',
    url: 'https://www.temu.com/mall.html?mall_id=synthetic_mall',
    host: 'temu.com',
    lastAnalyzedAt: '2026-07-07 09:00:00',
  },
  {
    has_fresh_data: true,
    latest_snapshot_at: '2026-07-07 09:00:00',
    latest_job_status: 'success',
    can_trigger_now: false,
    summary: {
      product_count: 4,
      new_launch_count: 1,
      sales_outlier_count: 1,
    },
    recent_launches: [
      {
        product_id: 'p-new',
        product_name: 'Synthetic New Listing',
        category: 'Synthetic',
        price: 12.5,
        daily_sales: 25,
        total_sales: 25,
        listed_at: '2026-07-07',
        url: 'https://www.temu.com/synthetic-new-listing',
      },
    ],
    sales_outliers: [
      {
        product_id: 'p-spike',
        product_name: 'Synthetic Spike',
        category: 'Synthetic',
        price: 19.9,
        daily_sales: 5000,
        total_sales: 5000,
        listed_at: '2026-07-07',
        url: 'https://www.temu.com/synthetic-spike',
        signal_value: '5000',
      },
    ],
    artifacts: {
      report_xlsx_path: 'reports/synthetic/report.xlsx',
    },
  },
  {
    snapshots: [
      { snapshot_id: 'ms_today', snapshot_at: '2026-07-07 09:00:00', product_count: 4 },
      { snapshot_id: 'ms_prev', snapshot_at: '2026-07-06 09:00:00', product_count: 3 },
    ],
    jobs: [
      { job_id: 'mj_done', status: 'success', finished_at: '2026-07-07 09:01:00' },
    ],
  },
)

assert.equal(report.summary.totalProducts, 4)
assert.equal(report.summary.recentListings, 1)
assert.equal(report.summary.salesSpikes, 1)
assert.equal(report.recentListings[0].name, 'Synthetic New Listing')
assert.equal(report.recentListings[0].priceText, '¥12.50')
assert.equal(report.salesSpikes[0].name, 'Synthetic Spike')
assert.equal(report.salesSpikes[0].severity, 'high')
assert.equal(report.previousCrawlDate, '2026-07-06')
assert.equal(report.artifacts.report_xlsx_path, 'reports/synthetic/report.xlsx')

console.log('temu_monitor_report_mapping_ok')
