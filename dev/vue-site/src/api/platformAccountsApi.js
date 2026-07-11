import { service } from './request'

/** Java API 使用 Jackson SNAKE_CASE，请求体字段需 snake_case */
function toBindPayload(payload) {
  const body = {
    platform: payload.platform,
    store_name: payload.storeName,
    account: payload.account,
    password: payload.password,
    company_name: payload.companyName,
  }
  if (payload.id) body.id = payload.id
  if (payload.platform === 'temu' || payload.externalShopId) {
    body.external_shop_id = payload.externalShopId || ''
  }
  return body
}

function mapStore(row) {
  if (!row) return row
  return {
    id: row.id,
    platform: row.platform,
    storeName: row.storeName || row.store_name,
    account: row.account,
    password: row.password || '',
    companyName: row.companyName || row.company_name || '',
    boundAt: row.boundAt || row.bound_at || '',
    externalShopId: row.externalShopId || row.external_shop_id || '',
    integrationMode: row.integrationMode || row.integration_mode || '',
    ziniaoBrowserOauth: row.ziniaoBrowserOauth || row.ziniao_browser_oauth || '',
    agentNodeId: row.agentNodeId || row.agent_node_id || '',
  }
}

function unwrapList(res) {
  if (Array.isArray(res)) return res
  if (Array.isArray(res?.data)) return res.data
  if (Array.isArray(res?.data?.data)) return res.data.data
  return []
}

export async function fetchBackendPlatformStores(platform) {
  const params = platform ? { platform } : {}
  const res = await service.get('/api/platform-accounts', { params, skipGlobalErrorToast: true })
  const rows = unwrapList(res)
  return { success: true, data: rows.map(mapStore) }
}

export async function bindBackendPlatformStore(payload) {
  const res = await service.post('/api/platform-accounts/bind', toBindPayload(payload))
  return {
    success: true,
    message: res?.message || '店铺绑定成功',
    data: mapStore(res?.data),
  }
}

export async function bindBackendPlatformStoresBatch(payload) {
  const res = await service.post('/api/platform-accounts/bind-batch', {
    company_name: payload.companyName,
    stores: (payload.stores || []).map((item) => toBindPayload({ ...item, companyName: payload.companyName })),
  })
  return {
    success: true,
    message: res?.message,
    data: (res?.data || []).map(mapStore),
    errors: res?.errors,
  }
}

export async function deleteBackendPlatformStore(id) {
  const res = await service.delete(`/api/platform-accounts/${id}`)
  return {
    success: true,
    message: res?.message || '店铺已解除绑定',
    data: mapStore(res?.data),
  }
}
