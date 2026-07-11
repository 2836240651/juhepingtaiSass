import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const here = dirname(fileURLToPath(import.meta.url))
const source = readFileSync(resolve(here, '../src/api/temuCompetitorsApi.js'), 'utf8')

assert.match(source, /service\.get\('\/api\/monitor\/targets'/)
assert.match(source, /service\.post\(`\/api\/monitor\/targets\/\$\{id\}\/trigger`/)
assert.match(source, /service\.get\(`\/api\/monitor\/targets\/\$\{id\}\/latest`/)
assert.match(source, /service\.get\(`\/api\/monitor\/targets\/\$\{id\}\/history`/)
assert.match(source, /force: !!normalized\.force/)
assert.doesNotMatch(source, /if \(latest\.has_fresh_data\) continue/)

console.log('temu_competitors_api_routes_ok')
