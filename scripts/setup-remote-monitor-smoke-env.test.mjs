import assert from 'node:assert/strict'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
const setup = require('./setup-remote-monitor-smoke-env.js')

const tokenEnv = setup.buildMonitorSmokeEnv({
  CROSSHUB_MONITOR_API_TOKEN: 'synthetic-token',
})
assert.match(tokenEnv, /^CROSSHUB_MONITOR_API_TOKEN=synthetic-token$/m)
assert.doesNotMatch(tokenEnv, /CROSSHUB_MONITOR_LOGIN_PASSWORD=.+/)

const loginEnv = setup.buildMonitorSmokeEnv({
  CROSSHUB_MONITOR_LOGIN_ACCOUNT: 'synthetic@example.test',
  CROSSHUB_MONITOR_LOGIN_PASSWORD: 'synthetic-password',
  CROSSHUB_MONITOR_PORTAL_ROLE: 'boss',
})
assert.match(loginEnv, /^CROSSHUB_MONITOR_LOGIN_ACCOUNT=synthetic@example.test$/m)
assert.match(loginEnv, /^CROSSHUB_MONITOR_LOGIN_PASSWORD=synthetic-password$/m)
assert.match(loginEnv, /^CROSSHUB_MONITOR_PORTAL_ROLE=boss$/m)

const quotedEnv = setup.buildMonitorSmokeEnv({
  CROSSHUB_MONITOR_LOGIN_ACCOUNT: 'synthetic@example.test',
  CROSSHUB_MONITOR_LOGIN_PASSWORD: "space value # $PATH ' quote",
})
assert.ok(quotedEnv.includes("CROSSHUB_MONITOR_LOGIN_PASSWORD='space value # $PATH '\\'' quote'\n"))

const missing = setup.validateConfig({
  CROSSHUB_SSH_HOST: 'synthetic-host',
  CROSSHUB_SSH_PASSWORD: 'synthetic-password',
})
assert.equal(missing.ok, false)
assert.ok(missing.missing.includes('CROSSHUB_MONITOR_API_TOKEN or CROSSHUB_MONITOR_LOGIN_ACCOUNT/CROSSHUB_MONITOR_LOGIN_PASSWORD'))

const ready = setup.validateConfig({
  CROSSHUB_SSH_HOST: 'synthetic-host',
  CROSSHUB_SSH_PASSWORD: 'synthetic-password',
  CROSSHUB_MONITOR_API_TOKEN: 'synthetic-token',
})
assert.equal(ready.ok, true)

console.log('setup_remote_monitor_smoke_env_ok')
