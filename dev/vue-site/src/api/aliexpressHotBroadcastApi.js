import { service } from './request'

function mapBroadcast(row) {
  if (!row) return row
  return {
    id: row.id,
    storeId: row.storeId || row.store_id || '',
    sku: row.sku || '',
    name: row.name || row.productName || row.product_name || '',
    dailySales: row.dailySales ?? row.daily_sales ?? 0,
    avg7DayDaily: row.avg7DayDaily ?? row.avg7_day_daily ?? 0,
    surgeRatio: row.surgeRatio ?? row.surge_ratio ?? 1,
    operator: row.operator || row.operator_name || '',
    time: row.time || row.broadcast_at || '',
    readBy: row.readBy || row.read_by || [],
    fromServer: Boolean(row.fromServer || row.from_server),
    source: row.source || 'manual',
    message: row.message || '',
  }
}

export async function fetchAliExpressHotBroadcasts({ storeId } = {}) {
  const params = {}
  if (storeId && storeId !== 'all') params.store_id = storeId
  const res = await service.get('/api/aliexpress/hot-broadcasts', { params, skipGlobalErrorToast: true })
  return (res?.data || []).map(mapBroadcast)
}

export async function createAliExpressHotBroadcast(payload) {
  const res = await service.post('/api/aliexpress/hot-broadcasts', {
    store_id: payload.storeId || '',
    sku: payload.sku,
    name: payload.name,
    daily_sales: payload.dailySales,
    avg7_day_daily: payload.avg7DayDaily,
    surge_ratio: payload.surgeRatio,
    operator: payload.operator,
    source: payload.source || 'manual',
    time: payload.time,
    message: payload.message || '爆款通报',
  })
  return mapBroadcast(res?.data)
}

export async function markAliExpressHotBroadcastRead(id, payload = {}) {
  const res = await service.post(`/api/aliexpress/hot-broadcasts/${id}/read`, {
    reader_id: payload.readerId || '',
    reader_name: payload.readerName || '',
  })
  return mapBroadcast(res?.data)
}
