import { fetchLocalEmployees } from './employeesLocal'
import {
  ensureDefaultUser,
  loginLocalBoss,
  registerLocalUser,
} from './authLocal'
import { isTemuBackendEnabled } from './config'
import { backendLogin } from './request'

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
        backendLinked: true,
        backendUserId: backend.user_id,
        backendRole: backend.role,
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
    },
  }
}

export async function loginEmployee({ account, password }) {
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

  const backend = await loginViaBackend(account, password, 'employee')

  return {
    success: true,
    data: {
      id: employee.id,
      name: employee.name,
      account: employee.account,
      role: employee.role,
      platforms: employee.platforms,
      assignedStoreIds: employee.assignedStoreIds || [],
      backendLinked: Boolean(backend),
      backendUserId: backend?.user_id || null,
      backendRole: backend?.role || '',
    },
  }
}
