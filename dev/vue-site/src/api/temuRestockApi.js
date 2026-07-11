import { service } from './request'

export function restockStatusKey(shopId, sku) {
  const shop = String(shopId || '').trim()
  const code = String(sku || '').trim()
  if (!code) return ''
  return shop ? `${shop}:${code}` : code
}

function mapRow(row) {
  const shopId = row.shopId || row.shop_id || ''
  const sku = row.sku || ''
  return {
    shopId,
    sku,
    status: row.status || 'pending',
    note: row.note || '',
    updatedAt: row.updatedAt || row.updated_at || '',
    updatedBy: row.updatedBy || row.updated_by || '',
  }
}

export function rowsToRestockStatusMap(rows = []) {
  const map = {}
  for (const row of rows) {
    const item = mapRow(row)
    if (!item.sku) continue
    const scopedKey = restockStatusKey(item.shopId, item.sku)
    map[scopedKey] = { status: item.status, note: item.note }
    if (!map[item.sku]) {
      map[item.sku] = { status: item.status, note: item.note }
    }
  }
  return map
}

export async function fetchBackendTemuRestockStatuses() {
  const res = await service.get('/api/temu/restock-status', { skipGlobalErrorToast: true })
  return (res?.data || []).map(mapRow)
}

export async function fetchBackendTemuRestockStatusMap() {
  const rows = await fetchBackendTemuRestockStatuses()
  return rowsToRestockStatusMap(rows)
}

export async function upsertBackendTemuRestockStatus(payload) {
  const res = await service.put('/api/temu/restock-status', {
    shop_id: payload.shopId || '',
    sku: payload.sku,
    status: payload.status,
    note: payload.note || '',
  })
  return mapRow(res?.data || payload)
}
