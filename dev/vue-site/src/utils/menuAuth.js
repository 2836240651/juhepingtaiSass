import {
  Briefcase,
  DataAnalysis,
  Goods,
  Key,
  Link,
  Sell,
  Shop,
  ShoppingBag,
  ShoppingCart,
  Tickets,
  TrendCharts,
  UserFilled,
  VideoCamera,
  VideoPlay,
} from '@element-plus/icons-vue'
import { employeeModuleMenus } from '@/utils/scope'

const MENU_ICONS = {
  'boss.employees': UserFilled,
  'boss.dashboard': TrendCharts,
  'boss.tasks': Tickets,
  'boss.accounts': Key,
  'employee.dashboard': TrendCharts,
  'employee.tasks': Briefcase,
  'employee.ai': DataAnalysis,
}

const PLATFORM_ICONS = {
  temu: Shop,
  aliexpress: Goods,
  amazon: Sell,
  walmart: ShoppingBag,
  pdd: ShoppingCart,
  douyin: VideoCamera,
  channels: VideoPlay,
  '1688': ShoppingCart,
  dtc: Link,
  shopify: Link,
  wordpress: Link,
}

export function iconForMenu(menu) {
  if (MENU_ICONS[menu.code]) return MENU_ICONS[menu.code]
  if (menu.platform && PLATFORM_ICONS[menu.platform]) return PLATFORM_ICONS[menu.platform]
  return Shop
}

export function decorateMenus(menus = []) {
  return (Array.isArray(menus) ? menus : []).map((menu) => ({
    ...menu,
    index: menu.path,
    icon: iconForMenu(menu),
  }))
}

export function fallbackSidebarMenus(auth) {
  if (auth.isBoss) {
    return decorateMenus([
      { code: 'boss.employees', path: '/boss/employees', label: '员工绑定', menu_type: 'admin' },
      { code: 'boss.dashboard', path: '/boss/dashboard', label: '运营总览', menu_type: 'admin' },
      { code: 'boss.tasks', path: '/boss/tasks', label: '任务分配', menu_type: 'admin' },
      { code: 'boss.platform.temu', path: '/boss/temu', label: 'Temu 运营', platform: 'temu', menu_type: 'module' },
      { code: 'boss.platform.aliexpress', path: '/boss/aliexpress', label: 'AliExpress 运营', platform: 'aliexpress', menu_type: 'module' },
      { code: 'boss.platform.amazon', path: '/boss/amazon', label: 'Amazon 运营', platform: 'amazon', menu_type: 'module' },
      { code: 'boss.platform.walmart', path: '/boss/walmart', label: 'Walmart 运营', platform: 'walmart', menu_type: 'module' },
      { code: 'boss.platform.pdd', path: '/boss/pdd', label: '拼多多运营', platform: 'pdd', menu_type: 'module' },
      { code: 'boss.platform.douyin', path: '/boss/douyin', label: '抖音运营', platform: 'douyin', menu_type: 'module' },
      { code: 'boss.platform.channels', path: '/boss/channels', label: '视频号运营', platform: 'channels', menu_type: 'module' },
      { code: 'boss.platform.1688', path: '/boss/1688', label: '1688 运营', platform: '1688', menu_type: 'module' },
      { code: 'boss.platform.dtc', path: '/boss/dtc', label: '独立站运营', platform: 'dtc', menu_type: 'module' },
      { code: 'boss.accounts', path: '/boss/accounts', label: '账户绑定', menu_type: 'admin' },
    ])
  }

  const platformMenus = employeeModuleMenus(auth).map((item) => ({
    code: `employee.platform.${item.platform}`,
    path: item.index,
    label: item.label,
    platform: item.platform,
    menu_type: 'module',
  }))

  return decorateMenus([
    { code: 'employee.dashboard', path: '/employee/dashboard', label: '我的工作台', menu_type: 'base' },
    ...platformMenus,
    { code: 'employee.tasks', path: '/employee/tasks', label: '任务中心', menu_type: 'base' },
    { code: 'employee.ai', path: '/employee/ai', label: 'AI 办公', menu_type: 'base' },
  ])
}

export function resolveSidebarMenus(auth) {
  const decorated = decorateMenus(auth.menus || [])
  if (decorated.length) return decorated
  return fallbackSidebarMenus(auth)
}

export function canAccessRoute(auth, to) {
  const record = [...to.matched].reverse().find((item) => item.meta?.menuCode)
  if (!record?.meta?.menuCode) return true

  if (auth.backendLinked) {
    return auth.hasMenuCode(record.meta.menuCode)
  }

  const requiredRole = to.matched.find((item) => item.meta.role)?.meta.role
  if (requiredRole && requiredRole !== auth.role) return false

  if (auth.isBoss) return true

  const allowedPaths = new Set(employeeModuleMenus(auth).map((item) => item.index))
  allowedPaths.add('/employee/dashboard')
  allowedPaths.add('/employee/tasks')
  allowedPaths.add('/employee/ai')
  return allowedPaths.has(to.path)
}

export function defaultLandingPath(auth) {
  const first = auth.menuPaths[0]
  if (first) return first
  return auth.isBoss ? '/boss/dashboard' : '/employee/dashboard'
}
