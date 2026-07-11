import { service } from './request'

function mapBroadcast(row) {
  if (!row) return row
  return {
    id: row.id,
    shopId: row.shopId || row.shop_id || '',
    sku: row.sku || '',
    name: row.name || row.product_name || '',
    dailySales: row.dailySales ?? row.daily_sales ?? 0,
    avg7DayDaily: row.avg7DayDaily ?? row.avg7_day_daily ?? 0,
    surgeRatio: row.surgeRatio ?? row.surge_ratio ?? 1,
    operator: row.operator || row.operator_name || '',
    time: row.time || row.broadcast_at || '',
    readBy: row.readBy || row.read_by || [],
    fromServer: Boolean(row.fromServer || row.from_server),
    source: row.source || 'manual',
  }
}

export async function fetchBackendHotBroadcasts() {
  const res = await service.get('/api/temu/hot-broadcasts', { skipGlobalErrorToast: true })
  return (res?.data || []).map(mapBroadcast)
}

export async function createBackendHotBroadcast(payload) {
  const res = await service.post('/api/temu/hot-broadcasts', {
    shop_id: payload.shopId || '',
    sku: payload.sku,
    name: payload.name,
    daily_sales: payload.dailySales,
    avg7_day_daily: payload.avg7DayDaily,
    surge_ratio: payload.surgeRatio,
    operator: payload.operator,
    source: payload.source || 'manual',
    time: payload.time,
  })
  return mapBroadcast(res?.data)
}

export async function markBackendHotBroadcastRead(id, payload = {}) {
  const res = await service.post(`/api/temu/hot-broadcasts/${id}/read`, {
    reader_id: payload.readerId || '',
    reader_name: payload.readerName || '',
  })
  return mapBroadcast(res?.data)
}
