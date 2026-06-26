import { isTemuBackendEnabled } from './config'
import { backendLogin } from './request'
import {
  ensureDefaultUser,
  loginLocalBoss,
  registerLocalUser,
} from './authLocal'
import { fetchLocalEmployees } from './employeesLocal'

function mapBackendSession(backend) {
  if (!backend) return {}
  return {
    backendLinked: true,
    backendUserId: backend.user_id,
    backendRole: backend.role,
    tenant_id: backend.tenant_id,
    menus: backend.menus || [],
    platforms: backend.platforms || [],
    shop_scope: backend.shop_scope || [],
  }
}

async function loginViaBackend(account, password, portalRole) {
  if (!isTemuBackendEnabled()) return null
  try {
    return await backendLogin(account, password, portalRole)
  } catch {
    return null
  }
}

export function registerCompany(payload) {
  const result = registerLocalUser(payload)
  if (result.error) throw new Error(result.error)
  return result
}

export async function loginBoss(payload) {
  const account = String(payload.account || '').trim()
  const password = String(payload.password || '')

  const backend = await loginViaBackend(account, password, 'boss')
  if (backend) {
    return {
      success: true,
      data: {
        company: backend.company || backend.nickname || '企业',
        account: backend.account || account,
        ...mapBackendSession(backend),
      },
    }
  }

  const result = loginLocalBoss({ account, password })
  if (result.error) throw new Error(result.error)
  return {
    success: true,
    data: {
      company: result.data.company,
      account: result.data.account,
      backendLinked: false,
      menus: [],
      platforms: [],
      shop_scope: [],
    },
  }
}

export async function loginEmployee({ account, password }) {
  const backend = await loginViaBackend(account, password, 'employee')
  if (backend) {
    return {
      success: true,
      data: {
        id: backend.user_id,
        name: backend.nickname || backend.account || account,
        account: backend.account || account,
        role: backend.job_title || backend.role || '',
        platforms: backend.platforms || [],
        assignedStoreIds: backend.shop_scope || [],
        backendLinked: true,
        backendUserId: backend.user_id || null,
        backendRole: backend.role || '',
        tenant_id: backend.tenant_id || null,
        menus: backend.menus || [],
        shop_scope: backend.shop_scope || [],
      },
    }
  }

  ensureDefaultUser()
  const acc = String(account || '').trim().toLowerCase()
  const pwd = String(password || '')
  const employees = fetchLocalEmployees().data || []
  const employee = employees.find(
    (e) => e.account.toLowerCase() === acc && e.password === pwd && e.status !== false,
  )
  if (!employee) {
    throw new Error('员工账号或密码错误，请联系管理员在员工绑定中添加')
  }

  return {
    success: true,
    data: {
      id: employee.id,
      name: employee.name,
      account: employee.account,
      role: employee.role,
      platforms: employee.platforms,
      assignedStoreIds: employee.assignedStoreIds || [],
      backendLinked: false,
      backendUserId: null,
      backendRole: '',
      tenant_id: null,
      menus: [],
      shop_scope: [],
    },
  }
}
