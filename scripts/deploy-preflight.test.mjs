import assert from 'node:assert/strict'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
const preflight = require('./deploy-preflight.js')

const usage = preflight.formatUsage()
assert.ok(usage.includes('Usage: node scripts/deploy-preflight.js [--json] [--help]'))
assert.ok(usage.includes('CROSSHUB_SSH_HOST'))
assert.ok(usage.includes('CROSSHUB_SSH_PASSWORD'))
assert.ok(usage.includes('CROSSHUB_REMOTE_MONITOR_SMOKE_ENV_READY=true'))
assert.ok(usage.includes('node scripts/setup-remote-monitor-smoke-env.js'))
assert.doesNotMatch(usage, /Bearer |mall_id=\d{6,}|CROSSHUB_(?:SSH_PASSWORD|MONITOR_API_TOKEN|MONITOR_LOGIN_PASSWORD)=.+/)

const missing = preflight.runPreflight({
  env: {},
  cwd: process.cwd(),
  checkGitIgnore: () => true,
  checkNodeModule: () => true,
})
assert.equal(missing.ok, false)
assert.ok(missing.missing.includes('CROSSHUB_SSH_HOST'))
assert.ok(missing.missing.includes('CROSSHUB_SSH_PASSWORD'))
const missingLines = preflight.formatPreflightResult(missing)
assert.ok(missingLines.includes('next_action=set CROSSHUB_SSH_HOST and CROSSHUB_SSH_PASSWORD in local environment'))
assert.ok(missingLines.includes('next_action=run node scripts/setup-remote-monitor-smoke-env.js then set CROSSHUB_REMOTE_MONITOR_SMOKE_ENV_READY=true'))
const missingPayload = preflight.toPreflightPayload(missing)
assert.equal(missingPayload.ok, false)
assert.ok(missingPayload.missing.includes('CROSSHUB_SSH_HOST'))
assert.ok(missingPayload.next_actions.includes('set CROSSHUB_SSH_HOST and CROSSHUB_SSH_PASSWORD in local environment'))

const ready = preflight.runPreflight({
  env: {
    CROSSHUB_SSH_HOST: 'synthetic-host',
    CROSSHUB_SSH_PASSWORD: 'synthetic-password',
    CROSSHUB_REMOTE_MONITOR_SMOKE_ENV_READY: 'true',
  },
  cwd: process.cwd(),
  checkGitIgnore: () => true,
  checkNodeModule: () => true,
})
assert.equal(ready.ok, true)
assert.equal(ready.missing.length, 0)
assert.ok(ready.checks.some((item) => item.name === 'remote_monitor_smoke_env_ready'))
assert.ok(ready.checks.some((item) => item.name === 'scripts/setup-remote-monitor-smoke-env.js'))
assert.ok(ready.checks.some((item) => item.name === 'scripts dependency ssh2'))
const readyLines = preflight.formatPreflightResult(ready)
assert.ok(readyLines.includes('deploy_preflight_ok'))
assert.ok(readyLines.includes('next_action=run node scripts/deploy-server.js'))
assert.doesNotMatch(readyLines, /synthetic-password|synthetic-token/)
const readyPayload = preflight.toPreflightPayload(ready)
assert.equal(readyPayload.ok, true)
assert.deepEqual(readyPayload.missing, [])
assert.deepEqual(readyPayload.next_actions, ['run node scripts/deploy-server.js'])
assert.doesNotMatch(JSON.stringify(readyPayload), /synthetic-password|synthetic-token/)

const noSmokeAuth = preflight.runPreflight({
  env: {
    CROSSHUB_SSH_HOST: 'synthetic-host',
    CROSSHUB_SSH_PASSWORD: 'synthetic-password',
  },
  cwd: process.cwd(),
  checkGitIgnore: () => true,
  checkNodeModule: () => true,
})
assert.equal(noSmokeAuth.ok, false)
assert.ok(noSmokeAuth.missing.includes('CROSSHUB_REMOTE_MONITOR_SMOKE_ENV_READY=true'))

const missingSsh2 = preflight.runPreflight({
  env: {
    CROSSHUB_SSH_HOST: 'synthetic-host',
    CROSSHUB_SSH_PASSWORD: 'synthetic-password',
    CROSSHUB_REMOTE_MONITOR_SMOKE_ENV_READY: 'true',
  },
  cwd: process.cwd(),
  checkGitIgnore: () => true,
  checkNodeModule: () => false,
})
assert.equal(missingSsh2.ok, false)
assert.ok(missingSsh2.missing.includes('scripts dependency ssh2'))
const missingSsh2Lines = preflight.formatPreflightResult(missingSsh2)
assert.ok(missingSsh2Lines.includes('next_action=run npm install in scripts directory'))

console.log('deploy_preflight_ok')
