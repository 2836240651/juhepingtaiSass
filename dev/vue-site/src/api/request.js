/**
 * Axios：对接本项目 Java Temu API（/api/temu、/api/auth）
 */
import axios from 'axios'
import { getActivePinia } from 'pinia'
import router from '@/router'
import { TEMU_API_BASE_URL } from './config'

export const service = axios.create({
  baseURL: import.meta.env.DEV ? '' : TEMU_API_BASE_URL,
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

export function getAccessToken() {
  return localStorage.getItem('accessToken') || null
}

export function setAccessToken(token) {
  localStorage.setItem('accessToken', token)
}

export function clearAccessToken() {
  localStorage.removeItem('accessToken')
}

function clearSession() {
  clearAccessToken()
  localStorage.removeItem('crosshub_logged_in')
  try {
    if (getActivePinia()) {
      import('@/stores/auth').then(({ useAuthStore }) => {
        useAuthStore().logout()
      })
    }
  } catch (_) {
    /* ignore */
  }
}

function pickMessage(data) {
  if (!data || typeof data !== 'object') return ''
  return String(data.msg || data.message || '').trim()
}

service.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

service.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res && typeof res === 'object' && 'code' in res && res.code !== 0 && res.code !== 200) {
      return Promise.reject(new Error(pickMessage(res) || '请求失败'))
    }
    return res
  },
  (error) => {
    const status = error.response?.status
    const msg = pickMessage(error.response?.data) || error.message || '请求失败'
    if (status === 401 && router.currentRoute.value?.path !== '/login') {
      clearSession()
      router.replace('/login')
    }
    return Promise.reject(new Error(msg))
  },
)

export async function backendLogin(account, password, portalRole) {
  const res = await service.post('/api/auth/login', {
    account,
    password,
    portal_role: portalRole,
  })
  const data = res?.data ?? res
  const token = data?.token
  if (!token) throw new Error('登录失败：未返回 token')
  setAccessToken(token)
  return data
}
