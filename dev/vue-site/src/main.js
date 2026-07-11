import './assets/main.css'
import 'element-plus/dist/index.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import App from './App.vue'
import router from './router'
import { ensureDemoStores } from './api/platformAccountsLocal'
import { ensureDemoEmployees } from './api/employeesLocal'
import { ensureDemoCompetitors } from './api/temuCompetitorsLocal'
import { ensureDemoWarehouseStaff } from './api/warehouseStaffLocal'
import { ensureDefaultUser } from './api/authLocal'
import { isTemuBackendEnabled } from './api/config'
import { clearAccessToken } from './api/request'

if (!isTemuBackendEnabled()) {
  clearAccessToken()
  localStorage.setItem('backend_linked', '0')
  ensureDefaultUser()
  ensureDemoStores()
  ensureDemoEmployees()
  ensureDemoWarehouseStaff()
  ensureDemoCompetitors()
} else if (localStorage.getItem('crosshub_logged_in') === '1' && !localStorage.getItem('accessToken')) {
  localStorage.setItem('crosshub_logged_in', '0')
  localStorage.setItem('backend_linked', '0')
}

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')
