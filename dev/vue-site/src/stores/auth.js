import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { clearAccessToken, fetchBackendSession } from '@/api/request'
import { decorateMenus, resolveSidebarMenus } from '@/utils/menuAuth'

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
  const tenantId = ref(Number(localStorage.getItem('backend_tenant_id') || 0) || null)
  const menus = ref(readJson('crosshub_menus', []))
  const platforms = ref(readJson('crosshub_platforms', []))
  const shopScope = ref(readJson('crosshub_shop_scope', []))

  const isBoss = computed(() => role.value === 'boss')
  const portalLabel = computed(() => (isBoss.value ? '企业管理员' : '员工端口'))
  const displayName = computed(() =>
    isBoss.value ? company.value.name : employee.value.name,
  )
  const sidebarMenus = computed(() => resolveSidebarMenus({
    menus: menus.value,
    isBoss: isBoss.value,
    backendLinked: backendLinked.value,
    employee: employee.value,
    platforms: platforms.value,
    role: role.value,
  }))
  const menuPaths = computed(() => sidebarMenus.value.map((item) => item.path))

  function persistSession() {
    localStorage.setItem('crosshub_logged_in', isLoggedIn.value ? '1' : '0')
    localStorage.setItem('crosshub_role', role.value)
    localStorage.setItem('crosshub_company', JSON.stringify(company.value))
    localStorage.setItem('crosshub_employee', JSON.stringify(employee.value))
    localStorage.setItem('backend_linked', backendLinked.value ? '1' : '0')
    localStorage.setItem('backend_role', backendRole.value || '')
    localStorage.setItem('crosshub_menus', JSON.stringify(menus.value))
    localStorage.setItem('crosshub_platforms', JSON.stringify(platforms.value))
    localStorage.setItem('crosshub_shop_scope', JSON.stringify(shopScope.value))
    if (backendUserId.value) {
      localStorage.setItem('backend_user_id', String(backendUserId.value))
    } else {
      localStorage.removeItem('backend_user_id')
    }
    if (tenantId.value) {
      localStorage.setItem('backend_tenant_id', String(tenantId.value))
    } else {
      localStorage.removeItem('backend_tenant_id')
    }
  }

  function applyBackendSession(payload = {}) {
    menus.value = Array.isArray(payload.menus) ? payload.menus : []
    platforms.value = Array.isArray(payload.platforms) ? payload.platforms : []
    shopScope.value = Array.isArray(payload.shop_scope) ? payload.shop_scope : []
    if (payload.tenant_id) tenantId.value = payload.tenant_id
    if (payload.user_id) backendUserId.value = payload.user_id
    if (payload.role) backendRole.value = payload.role
    backendLinked.value = true
    persistSession()
  }

  function setCompany(payload) {
    company.value = {
      name: payload.company || payload.name,
      account: payload.account,
    }
    if (payload.backendRole) backendRole.value = payload.backendRole
    if (payload.backendUserId) backendUserId.value = payload.backendUserId
    if (payload.backendLinked !== undefined) backendLinked.value = Boolean(payload.backendLinked)
    if (payload.menus) menus.value = payload.menus
    if (payload.platforms) platforms.value = payload.platforms
    if (payload.shop_scope) shopScope.value = payload.shop_scope
    if (payload.tenant_id) tenantId.value = payload.tenant_id
    persistSession()
  }

  function setEmployee(payload) {
    employee.value = {
      id: payload.id || '',
      name: payload.name,
      account: payload.account,
      role: payload.role,
      platforms: payload.platforms || [],
      assignedStoreIds: payload.assignedStoreIds || payload.shop_scope || [],
    }
    if (payload.backendRole) backendRole.value = payload.backendRole
    if (payload.backendUserId) backendUserId.value = payload.backendUserId
    if (payload.backendLinked !== undefined) backendLinked.value = Boolean(payload.backendLinked)
    if (payload.menus) menus.value = payload.menus
    if (payload.platforms) platforms.value = payload.platforms
    if (payload.shop_scope) shopScope.value = payload.shop_scope
    if (payload.tenant_id) tenantId.value = payload.tenant_id
    persistSession()
  }

  function hasMenuCode(code) {
    return menus.value.some((item) => item.code === code)
  }

  async function refreshSession() {
    if (!backendLinked.value) return
    const data = await fetchBackendSession()
    applyBackendSession(data)
    if (!isBoss.value && data) {
      employee.value = {
        ...employee.value,
        platforms: data.platforms || employee.value.platforms,
        assignedStoreIds: data.shop_scope || employee.value.assignedStoreIds,
      }
      persistSession()
    }
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
    tenantId.value = null
    menus.value = []
    platforms.value = []
    shopScope.value = []
    clearAccessToken()
    localStorage.removeItem('crosshub_logged_in')
    localStorage.removeItem('backend_linked')
    localStorage.removeItem('backend_role')
    localStorage.removeItem('backend_user_id')
    localStorage.removeItem('backend_tenant_id')
    localStorage.removeItem('crosshub_menus')
    localStorage.removeItem('crosshub_platforms')
    localStorage.removeItem('crosshub_shop_scope')
  }

  return {
    isLoggedIn,
    role,
    company,
    employee,
    backendLinked,
    backendUserId,
    backendRole,
    tenantId,
    menus,
    platforms,
    shopScope,
    isBoss,
    portalLabel,
    displayName,
    sidebarMenus,
    menuPaths,
    setCompany,
    setEmployee,
    applyBackendSession,
    hasMenuCode,
    refreshSession,
    login,
    logout,
  }
})
