import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { clearAccessToken } from '@/api/request'

function readJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

export const useAuthStore = defineStore('auth', () => {
  const isLoggedIn = ref(localStorage.getItem('crosshub_logged_in') === '1')
  const role = ref(localStorage.getItem('crosshub_role') || 'boss')
  const company = ref(
    readJson('crosshub_company', {
      name: '泰州亿拓户外用品有限公司',
      account: 'admin@crosshub.cn',
    }),
  )
  const employee = ref(
    readJson('crosshub_employee', {
      id: '',
      name: '',
      account: '',
      role: '',
      platforms: [],
      assignedStoreIds: [],
    }),
  )
  const backendLinked = ref(localStorage.getItem('backend_linked') === '1')
  const backendUserId = ref(Number(localStorage.getItem('backend_user_id') || 0) || null)
  const backendRole = ref(localStorage.getItem('backend_role') || '')

  const isBoss = computed(() => role.value === 'boss')
  const portalLabel = computed(() => (isBoss.value ? '企业管理员' : '员工端口'))
  const displayName = computed(() =>
    isBoss.value ? company.value.name : employee.value.name,
  )

  function persistSession() {
    localStorage.setItem('crosshub_logged_in', isLoggedIn.value ? '1' : '0')
    localStorage.setItem('crosshub_role', role.value)
    localStorage.setItem('crosshub_company', JSON.stringify(company.value))
    localStorage.setItem('crosshub_employee', JSON.stringify(employee.value))
    localStorage.setItem('backend_linked', backendLinked.value ? '1' : '0')
    localStorage.setItem('backend_role', backendRole.value || '')
    if (backendUserId.value) {
      localStorage.setItem('backend_user_id', String(backendUserId.value))
    } else {
      localStorage.removeItem('backend_user_id')
    }
  }

  function setCompany(payload) {
    company.value = {
      name: payload.company || payload.name,
      account: payload.account,
    }
    if (payload.backendRole) backendRole.value = payload.backendRole
    if (payload.backendUserId) backendUserId.value = payload.backendUserId
    backendLinked.value = Boolean(payload.backendLinked)
    persistSession()
  }

  function setEmployee(payload) {
    employee.value = {
      id: payload.id || '',
      name: payload.name,
      account: payload.account,
      role: payload.role,
      platforms: payload.platforms || [],
      assignedStoreIds: payload.assignedStoreIds || [],
    }
    if (payload.backendRole) backendRole.value = payload.backendRole
    if (payload.backendUserId) backendUserId.value = payload.backendUserId
    backendLinked.value = Boolean(payload.backendLinked)
    persistSession()
  }

  function login(nextRole) {
    role.value = nextRole
    isLoggedIn.value = true
    persistSession()
  }

  function logout() {
    isLoggedIn.value = false
    backendLinked.value = false
    backendRole.value = ''
    backendUserId.value = null
    clearAccessToken()
    localStorage.removeItem('crosshub_logged_in')
    localStorage.removeItem('backend_linked')
    localStorage.removeItem('backend_role')
    localStorage.removeItem('backend_user_id')
  }

  return {
    isLoggedIn,
    role,
    company,
    employee,
    backendLinked,
    backendUserId,
    backendRole,
    isBoss,
    portalLabel,
    displayName,
    setCompany,
    setEmployee,
    login,
    logout,
  }
})
