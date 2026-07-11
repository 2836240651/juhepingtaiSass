import assert from 'node:assert/strict'
import { resolveAppError } from '../src/utils/appErrorCode.js'

const sourceUnavailable = resolveAppError({
  errorCode: 'MONITOR_SOURCE_UNAVAILABLE',
  message: 'Temu snapshots require boards/ctf-website page-card evidence.',
})

assert.equal(sourceUnavailable.title, '缺少页面卡片证据')
assert.match(sourceUnavailable.summary, /页面卡片证据/)
assert.ok(sourceUnavailable.steps.some((step) => step.includes('raw_products.json')))

const invalidUrl = resolveAppError({
  errorCode: 'MONITOR_INVALID_URL',
  message: 'Temu provider requires a valid temu.com mall URL.',
})

assert.equal(invalidUrl.title, '竞店链接无效')
assert.match(invalidUrl.summary, /Temu 店铺链接/)

const legacyDisabled = resolveAppError({
  errorCode: 'MONITOR_LEGACY_ANALYZE_DISABLED',
  message: '旧竞店分析入口已停用，请使用 /api/monitor 任务链路',
})

assert.equal(legacyDisabled.title, '旧竞店分析入口已停用')
assert.match(legacyDisabled.summary, /\/api\/monitor/)

console.log('monitor_error_copy_ok')
