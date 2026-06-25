const STORAGE_KEY = 'crosshub_temu_hot_broadcasts'

export function loadHotBroadcasts() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function saveHotBroadcasts(list) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
}

export function appendHotBroadcast(entry) {
  const list = loadHotBroadcasts()
  list.unshift(entry)
  saveHotBroadcasts(list)
  return list
}

export function markBroadcastRead(broadcastId, readerName) {
  const list = loadHotBroadcasts().map((item) => {
    if (item.id !== broadcastId) return item
    const readBy = new Set(item.readBy || [])
    if (readerName) readBy.add(readerName)
    return { ...item, readBy: [...readBy] }
  })
  saveHotBroadcasts(list)
  return list
}

/** 从后端爆款列表生成初始通报种子 */
export function seedBroadcastsFromOverload(products = []) {
  const existing = loadHotBroadcasts()
  if (existing.length) return existing

  const seeds = products
    .filter((p) => p.isOverload || p.isHot)
    .slice(0, 5)
    .map((p, index) => ({
      id: `overload-${p.sku}-${index}`,
      time: new Date().toLocaleString('zh-CN', { hour12: false }),
      sku: p.sku,
      name: p.name,
      dailySales: p.dailySales,
      avg7DayDaily: p.avg7DayDaily,
      surgeRatio: p.surgeRatio,
      operator: '后端爆款榜',
      readBy: [],
      fromServer: true,
    }))

  if (seeds.length) saveHotBroadcasts(seeds)
  return seeds.length ? seeds : existing
}
