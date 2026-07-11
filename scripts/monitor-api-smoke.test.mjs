import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import { mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const require = createRequire(import.meta.url)
const smoke = require('./monitor-api-smoke.js')

const target = smoke.buildSyntheticTargetPayload()
assert.equal(target.platform, 'temu')
assert.equal(target.target_type, 'shop')
assert.equal(target.target_url, 'https://www.temu.com/mall.html?mall_id=synthetic_api_smoke')
assert.doesNotMatch(target.target_url, /mall_id=\d{6,}/)

const products = smoke.buildSyntheticProducts()
assert.equal(products.length, 4)
assert.deepEqual(products.map((item) => item.goods_id), ['1001', '1002', '1003', '1004'])
assert.ok(products.every((item) => item.href.includes('synthetic-api-smoke')))

const paths = smoke.buildApiPaths('mt_synthetic_api_smoke', 'mj_synthetic_api_smoke')
assert.equal(paths.createTarget, '/api/monitor/targets')
assert.equal(paths.triggerTarget, '/api/monitor/targets/mt_synthetic_api_smoke/trigger')
assert.equal(paths.getJob, '/api/monitor/jobs/mj_synthetic_api_smoke')
assert.equal(paths.getLatest, '/api/monitor/targets/mt_synthetic_api_smoke/latest')

const parsed = smoke.parseArgs(['--api-token', 'synthetic-token'])
assert.equal(parsed.apiToken, 'synthetic-token')

const loginParsed = smoke.parseArgs([
  '--login-account',
  'synthetic@example.test',
  '--login-password',
  'synthetic-password',
  '--portal-role',
  'boss',
])
assert.equal(loginParsed.loginAccount, 'synthetic@example.test')
assert.equal(loginParsed.loginPassword, 'synthetic-password')
assert.equal(loginParsed.portalRole, 'boss')

const loginPayload = smoke.buildLoginPayload(loginParsed)
assert.deepEqual(loginPayload, {
  account: 'synthetic@example.test',
  password: 'synthetic-password',
  portal_role: 'boss',
})

const dir = mkdtempSync(join(tmpdir(), 'crosshub-monitor-api-smoke-'))
try {
  const evidenceFile = smoke.writeSyntheticEvidence(dir, 'mt_synthetic_api_smoke')
  assert.equal(evidenceFile.replace(/\\/g, '/'), `${dir.replace(/\\/g, '/')}/mt_synthetic_api_smoke/raw_products.json`)
} finally {
  rmSync(dir, { recursive: true, force: true })
}

console.log('monitor_api_smoke_script_ok')
