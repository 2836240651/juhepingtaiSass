#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..');

function exists(relPath, cwd = ROOT) {
  return fs.existsSync(path.resolve(cwd, relPath));
}

function defaultCheckGitIgnore(pattern, cwd = ROOT) {
  const result = spawnSync('git', ['check-ignore', pattern], {
    cwd,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  return result.status === 0;
}

function defaultCheckNodeModule(moduleName, cwd = ROOT) {
  try {
    require.resolve(moduleName, {
      paths: [
        path.resolve(cwd, 'scripts/node_modules'),
        path.resolve(cwd, 'scripts'),
        cwd,
      ],
    });
    return true;
  } catch (_) {
    return false;
  }
}

function remoteMonitorSmokeEnvReady(env) {
  return String(env.CROSSHUB_REMOTE_MONITOR_SMOKE_ENV_READY || '').toLowerCase() === 'true';
}

function runPreflight({
  env = process.env,
  cwd = ROOT,
  checkGitIgnore = defaultCheckGitIgnore,
  checkNodeModule = defaultCheckNodeModule,
} = {}) {
  const checks = [];
  const missing = [];

  addEnvCheck(checks, missing, env, 'CROSSHUB_SSH_HOST');
  addEnvCheck(checks, missing, env, 'CROSSHUB_SSH_PASSWORD');
  addFileCheck(checks, missing, cwd, 'scripts/deploy-server.js');
  addFileCheck(checks, missing, cwd, 'scripts/monitor-api-smoke.js');
  addFileCheck(checks, missing, cwd, 'scripts/setup-remote-monitor-smoke-env.js');
  addFileCheck(checks, missing, cwd, 'deploy/monitor-smoke.env.example');
  addFileCheck(checks, missing, cwd, 'deploy/Dockerfile.python-worker');
  addFileCheck(checks, missing, cwd, 'deploy/docker-compose.yml');
  addNodeModuleCheck(checks, missing, cwd, 'ssh2', checkNodeModule);

  const smokeEnvReady = remoteMonitorSmokeEnvReady(env);
  checks.push({ name: 'remote_monitor_smoke_env_ready', ok: smokeEnvReady });
  if (!smokeEnvReady) {
    missing.push('CROSSHUB_REMOTE_MONITOR_SMOKE_ENV_READY=true');
  }

  const ignored = checkGitIgnore('.monitor-smoke.env', cwd);
  checks.push({ name: 'monitor_smoke_env_gitignored', ok: ignored });
  if (!ignored) {
    missing.push('.monitor-smoke.env gitignore rule');
  }

  const templateSafe = monitorSmokeTemplateIsSafe(cwd);
  checks.push({ name: 'monitor_smoke_env_template_safe', ok: templateSafe });
  if (!templateSafe) {
    missing.push('safe deploy/monitor-smoke.env.example');
  }

  return { ok: missing.length === 0, missing, checks };
}

function addEnvCheck(checks, missing, env, name) {
  const ok = Boolean(env[name]);
  checks.push({ name, ok });
  if (!ok) missing.push(name);
}

function addFileCheck(checks, missing, cwd, relPath) {
  const ok = exists(relPath, cwd);
  checks.push({ name: relPath, ok });
  if (!ok) missing.push(relPath);
}

function addNodeModuleCheck(checks, missing, cwd, moduleName, checkNodeModule) {
  const name = `scripts dependency ${moduleName}`;
  const ok = checkNodeModule(moduleName, cwd);
  checks.push({ name, ok });
  if (!ok) missing.push(name);
}

function monitorSmokeTemplateIsSafe(cwd = ROOT) {
  const templatePath = path.resolve(cwd, 'deploy/monitor-smoke.env.example');
  if (!fs.existsSync(templatePath)) return false;
  const template = fs.readFileSync(templatePath, 'utf8');
  return (
    template.includes('CROSSHUB_MONITOR_API_TOKEN=')
    && template.includes('CROSSHUB_MONITOR_LOGIN_ACCOUNT=')
    && template.includes('CROSSHUB_MONITOR_LOGIN_PASSWORD=')
    && !template.includes('12345678')
    && !/Bearer\s+\S+/.test(template)
    && !/mall_id=\d{6,}/.test(template)
  );
}

function formatPreflightResult(result) {
  const lines = [];
  for (const check of result.checks) {
    lines.push(`${check.ok ? 'ok' : 'missing'} ${check.name}`);
  }
  if (!result.ok) {
    lines.push(`deploy_preflight_failed=${result.missing.join(',')}`);
    for (const action of nextActionsForMissing(result.missing)) {
      lines.push(`next_action=${action}`);
    }
  } else {
    lines.push('deploy_preflight_ok');
    lines.push('next_action=run node scripts/deploy-server.js');
  }
  return lines.join('\n');
}

function formatUsage() {
  return [
    'Usage: node scripts/deploy-preflight.js [--json] [--help]',
    '',
    'Checks production deployment prerequisites for crosshub-python-worker monitor alignment.',
    '',
    'Options:',
    '  --json   Print machine-readable ok/missing/checks/next_actions.',
    '  --help   Print this help text.',
    '',
    'Required local environment:',
    '  CROSSHUB_SSH_HOST',
    '  CROSSHUB_SSH_PASSWORD',
    '  CROSSHUB_REMOTE_MONITOR_SMOKE_ENV_READY=true',
    '',
    'Prepare remote smoke env first:',
    '  node scripts/setup-remote-monitor-smoke-env.js',
  ].join('\n');
}

function toPreflightPayload(result) {
  return {
    ok: result.ok,
    missing: [...result.missing],
    checks: result.checks.map((check) => ({ name: check.name, ok: check.ok })),
    next_actions: result.ok ? ['run node scripts/deploy-server.js'] : nextActionsForMissing(result.missing),
  };
}

function nextActionsForMissing(missing) {
  const missingSet = new Set(missing);
  const actions = [];
  if (missingSet.has('CROSSHUB_SSH_HOST') || missingSet.has('CROSSHUB_SSH_PASSWORD')) {
    actions.push('set CROSSHUB_SSH_HOST and CROSSHUB_SSH_PASSWORD in local environment');
  }
  if (missingSet.has('scripts dependency ssh2')) {
    actions.push('run npm install in scripts directory');
  }
  if (missingSet.has('CROSSHUB_REMOTE_MONITOR_SMOKE_ENV_READY=true')) {
    actions.push('run node scripts/setup-remote-monitor-smoke-env.js then set CROSSHUB_REMOTE_MONITOR_SMOKE_ENV_READY=true');
  }
  if (missingSet.has('.monitor-smoke.env gitignore rule')) {
    actions.push('add .monitor-smoke.env to .gitignore before writing private smoke env');
  }
  if (missingSet.has('safe deploy/monitor-smoke.env.example')) {
    actions.push('restore deploy/monitor-smoke.env.example without real credentials or target identifiers');
  }
  return actions;
}

function printResult(result, options = {}) {
  const output = options.json
    ? JSON.stringify(toPreflightPayload(result), null, 2)
    : formatPreflightResult(result);
  if (result.ok) {
    console.log(output);
  } else {
    console.error(output);
  }
}

function main(argv = process.argv.slice(2)) {
  if (argv.includes('--help')) {
    console.log(formatUsage());
    process.exit(0);
  }
  const result = runPreflight();
  printResult(result, { json: argv.includes('--json') });
  process.exit(result.ok ? 0 : 1);
}

if (require.main === module) {
  main();
}

module.exports = {
  defaultCheckNodeModule,
  remoteMonitorSmokeEnvReady,
  monitorSmokeTemplateIsSafe,
  formatPreflightResult,
  formatUsage,
  toPreflightPayload,
  nextActionsForMissing,
  runPreflight,
};
