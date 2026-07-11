import { setLocalTenantId } from '@/utils/tenantStorage'

const STORAGE_KEY = 'crosshub_auth_users'

const DEFAULT_USER = {
  id: 'demo_company_1',
  company: '泰州亿拓户外用品有限公司',
  account: 'admin@crosshub.cn',
  password: '12345678',
  createdAt: '2026-06-18 09:00:00',
}

function loadAll() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveAll(users) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(users))
}

function createId() {
  return `user_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
}

function nextLocalTenantId() {
  const key = 'crosshub_local_tenant_seq'
  const next = Number(localStorage.getItem(key) || 1000) + 1
  localStorage.setItem(key, String(next))
  return next
}

/** 确保默认演示账号存在 */
export function ensureDefaultUser() {
  const users = loadAll()
  if (users.some((u) => u.account === DEFAULT_USER.account)) return
  saveAll([{ ...DEFAULT_USER, tenant_id: 1 }, ...users])
}

export function findUserByAccount(account) {
  ensureDefaultUser()
  const acc = String(account || '').trim().toLowerCase()
  return loadAll().find((u) => u.account.toLowerCase() === acc) || null
}

export function registerLocalUser({ company, account, password }) {
  ensureDefaultUser()

  const companyName = String(company || '').trim()
  const acc = String(account || '').trim()
  const pwd = String(password || '')

  if (!companyName) return { error: '请填写企业名称' }
  if (!acc) return { error: '请填写登录账号' }
  if (pwd.length < 6) return { error: '密码至少 6 位' }

  const users = loadAll()
  if (users.some((u) => u.account.toLowerCase() === acc.toLowerCase())) {
    return { error: '该账号已注册，请直接登录' }
  }

  const tenantId = nextLocalTenantId()
  const user = {
    id: createId(),
    tenant_id: tenantId,
    company: companyName,
    account: acc,
    password: pwd,
    createdAt: new Date().toISOString().replace('T', ' ').slice(0, 19),
  }
  users.push(user)
  saveAll(users)
  setLocalTenantId(tenantId)
  return { success: true, data: { ...user, password: undefined } }
}

export function loginLocalBoss({ account, password }) {
  const user = findUserByAccount(account)
  if (!user) return { error: '账号不存在，请先注册' }
  if (user.password !== password) return { error: '密码错误' }
  if (user.tenant_id) setLocalTenantId(user.tenant_id)
  return {
    success: true,
    data: {
      id: user.id,
      tenant_id: user.tenant_id || null,
      company: user.company,
      account: user.account,
    },
  }
}
