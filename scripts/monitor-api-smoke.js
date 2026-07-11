#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..');

function buildSyntheticTargetPayload() {
  return {
    platform: 'temu',
    target_type: 'shop',
    label: 'Synthetic API Smoke Store',
    target_url: 'https://www.temu.com/mall.html?mall_id=synthetic_api_smoke',
    freshness_minutes: 1440,
    crawl_strategy: 'store_listing',
    status: 'active',
  };
}

function buildSyntheticProducts() {
  return [
    syntheticProduct('1001', 'Synthetic API Smoke Baseline', 500, 20),
    syntheticProduct('1002', 'Synthetic API Smoke Stable', 650, 25),
    syntheticProduct('1003', 'Synthetic API Smoke Rising', 900, 30),
    syntheticProduct('1004', 'Synthetic API Smoke Outlier', 1200, 5000),
  ];
}

function syntheticProduct(goodsId, title, priceYen, soldNum) {
  const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  return {
    goods_id: goodsId,
    title,
    price_yen: priceYen,
    sold_num: soldNum,
    sold_text: String(soldNum),
    href: `https://www.temu.com/jp-zh-Hans/synthetic-api-smoke-${slug}-g-${goodsId}.html`,
  };
}

function buildApiPaths(targetId, jobId) {
  return {
    createTarget: '/api/monitor/targets',
    updateSchedule: `/api/monitor/targets/${targetId}/schedule`,
    triggerTarget: `/api/monitor/targets/${targetId}/trigger`,
    getJob: `/api/monitor/jobs/${jobId}`,
    getLatest: `/api/monitor/targets/${targetId}/latest`,
  };
}

function writeSyntheticEvidence(evidenceRoot, targetId) {
  const targetDir = path.join(evidenceRoot, targetId);
  fs.mkdirSync(targetDir, { recursive: true });
  const evidenceFile = path.join(targetDir, 'raw_products.json');
  fs.writeFileSync(evidenceFile, JSON.stringify(buildSyntheticProducts(), null, 2), 'utf8');
  return evidenceFile;
}

function parseArgs(argv) {
  const options = {
    baseUrl: process.env.CROSSHUB_MONITOR_API_BASE || 'http://127.0.0.1:18080',
    evidenceRoot: process.env.CROSSHUB_MONITOR_EVIDENCE_DIR || path.join(ROOT, 'backend/python/exports/ctf-website'),
    dbPath: process.env.CROSSHUB_DB_PATH || path.join(ROOT, 'backend/data/crosshub.db'),
    python: process.env.CROSSHUB_PYTHON || (process.platform === 'win32' ? 'py' : 'python3'),
    pythonDir: process.env.CROSSHUB_PYTHON_DIR || path.join(ROOT, 'backend/python'),
    reportRoot: process.env.CROSSHUB_MONITOR_REPORT_ROOT || 'reports',
    timeoutMs: Number(process.env.CROSSHUB_MONITOR_SMOKE_TIMEOUT_MS || 30000),
    apiToken: process.env.CROSSHUB_MONITOR_API_TOKEN || '',
    loginAccount: process.env.CROSSHUB_MONITOR_LOGIN_ACCOUNT || '',
    loginPassword: process.env.CROSSHUB_MONITOR_LOGIN_PASSWORD || '',
    portalRole: process.env.CROSSHUB_MONITOR_PORTAL_ROLE || 'boss',
    localWorker: undefined,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--base-url') options.baseUrl = argv[++i];
    else if (arg === '--evidence-root') options.evidenceRoot = argv[++i];
    else if (arg === '--db-path') options.dbPath = argv[++i];
    else if (arg === '--python') options.python = argv[++i];
    else if (arg === '--python-dir') options.pythonDir = argv[++i];
    else if (arg === '--report-root') options.reportRoot = argv[++i];
    else if (arg === '--timeout-ms') options.timeoutMs = Number(argv[++i]);
    else if (arg === '--api-token') options.apiToken = argv[++i];
    else if (arg === '--login-account') options.loginAccount = argv[++i];
    else if (arg === '--login-password') options.loginPassword = argv[++i];
    else if (arg === '--portal-role') options.portalRole = argv[++i];
    else if (arg === '--run-local-worker') options.localWorker = true;
    else if (arg === '--no-local-worker') options.localWorker = false;
    else if (arg === '--help') {
      printHelp();
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  if (options.localWorker === undefined) {
    options.localWorker = isLocalBaseUrl(options.baseUrl);
  }
  return options;
}

function buildLoginPayload(options) {
  return {
    account: options.loginAccount,
    password: options.loginPassword,
    portal_role: options.portalRole || 'boss',
  };
}

function isLocalBaseUrl(baseUrl) {
  const host = new URL(baseUrl).hostname;
  return host === '127.0.0.1' || host === 'localhost' || host === '::1';
}

async function apiRequest(baseUrl, method, pathname, body, apiToken = '') {
  const url = new URL(pathname, baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`);
  const headers = {};
  if (body) headers['content-type'] = 'application/json';
  if (apiToken) headers.authorization = `Bearer ${apiToken}`;
  const response = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await response.text();
  let payload = {};
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch (error) {
      throw new Error(`${method} ${pathname} returned non-JSON response: ${text.slice(0, 200)}`);
    }
  }
  if (!response.ok || payload.code !== 0) {
    throw new Error(`${method} ${pathname} failed: HTTP ${response.status} ${text.slice(0, 300)}`);
  }
  return payload.data;
}

async function resolveApiToken(options) {
  if (options.apiToken) return options.apiToken;
  if (!options.loginAccount || !options.loginPassword) return '';
  const data = await apiRequest(options.baseUrl, 'POST', '/api/auth/login', buildLoginPayload(options));
  const token = String(data.token || '');
  if (!token) {
    throw new Error('/api/auth/login did not return data.token');
  }
  return token;
}

function runLocalWorkerOnce(options) {
  const env = {
    ...process.env,
    CROSSHUB_DB_PATH: options.dbPath,
    CROSSHUB_MONITOR_EVIDENCE_DIR: options.evidenceRoot,
    PYTHONUNBUFFERED: '1',
  };
  const result = spawnSync(
    options.python,
    ['monitor_worker.py', '--once', '--json', '--worker-id', 'monitor-api-smoke', '--report-root', options.reportRoot],
    {
      cwd: options.pythonDir,
      env,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
    },
  );
  if (result.status !== 0) {
    throw new Error(`monitor_worker.py failed:\n${result.stdout}\n${result.stderr}`);
  }
  return (result.stdout || '').trim();
}

async function waitForLatest(options, targetId) {
  const baseUrl = options.baseUrl;
  const timeoutMs = options.timeoutMs;
  const deadline = Date.now() + timeoutMs;
  let latest = null;
  while (Date.now() <= deadline) {
    latest = await apiRequest(baseUrl, 'GET', buildApiPaths(targetId, 'unused').getLatest, undefined, options.apiToken);
    const summary = latest.summary || {};
    if (latest.has_fresh_data && Number(summary.product_count || 0) >= 4) {
      return latest;
    }
    await sleep(1000);
  }
  throw new Error(`Timed out waiting for fresh monitor snapshot. Last latest payload: ${JSON.stringify(latest)}`);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function runSmoke(options) {
  options.apiToken = await resolveApiToken(options);
  const target = await apiRequest(options.baseUrl, 'POST', '/api/monitor/targets', buildSyntheticTargetPayload(), options.apiToken);
  const targetId = String(target.id);
  writeSyntheticEvidence(options.evidenceRoot, targetId);
  await apiRequest(options.baseUrl, 'PUT', buildApiPaths(targetId, 'unused').updateSchedule, {
    enabled: true,
    schedule_type: 'interval',
    interval_minutes: 720,
    max_products: 100,
    retry_limit: 1,
  }, options.apiToken);
  const job = await apiRequest(options.baseUrl, 'POST', buildApiPaths(targetId, 'unused').triggerTarget, {
    reason: 'synthetic api smoke',
  }, options.apiToken);
  const workerOutput = options.localWorker ? runLocalWorkerOnce(options) : '';
  const latest = await waitForLatest(options, targetId);
  return {
    status: 'ok',
    target_id: targetId,
    job_id: job.job_id,
    snapshot_id: latest.latest_snapshot_id,
    product_count: latest.summary.product_count,
    recent_launch_count: latest.summary.new_launch_count,
    sales_outlier_count: latest.summary.sales_outlier_count,
    local_worker_ran: options.localWorker,
    worker_output: workerOutput,
  };
}

function printHelp() {
  console.log(`
Usage: node scripts/monitor-api-smoke.js [options]

Creates a synthetic Temu monitor target, writes synthetic boards/ctf-website page-card evidence,
triggers /api/monitor, optionally runs the local Python worker, and waits for a fresh latest snapshot.

Options:
  --base-url <url>       Java API base URL, default CROSSHUB_MONITOR_API_BASE or http://127.0.0.1:18080
  --evidence-root <dir>  Evidence root, default CROSSHUB_MONITOR_EVIDENCE_DIR or backend/python/exports/ctf-website
  --db-path <file>       SQLite DB path for local worker, default CROSSHUB_DB_PATH or backend/data/crosshub.db
  --python <cmd>         Python executable for local worker
  --python-dir <dir>     backend/python directory for local worker
  --report-root <dir>    Worker report root relative to backend/python
  --timeout-ms <ms>      Wait timeout for latest snapshot
  --api-token <token>    Optional bearer token, default CROSSHUB_MONITOR_API_TOKEN
  --login-account <acct> Optional account for /api/auth/login, default CROSSHUB_MONITOR_LOGIN_ACCOUNT
  --login-password <pwd> Optional password for /api/auth/login, default CROSSHUB_MONITOR_LOGIN_PASSWORD
  --portal-role <role>   Login portal role, default CROSSHUB_MONITOR_PORTAL_ROLE or boss
  --run-local-worker     Force running local worker once
  --no-local-worker      Do not run local worker; wait for deployed worker
`);
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const result = await runSmoke(options);
  console.log(JSON.stringify(result, null, 2));
}

if (require.main === module) {
  main().catch((error) => {
    console.error(error.message || error);
    process.exit(1);
  });
}

module.exports = {
  buildLoginPayload,
  buildApiPaths,
  buildSyntheticProducts,
  buildSyntheticTargetPayload,
  parseArgs,
  runSmoke,
  writeSyntheticEvidence,
};
