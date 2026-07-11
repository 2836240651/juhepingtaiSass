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

/** @deprecated 种子数据模式已关闭，仅返回已有本地通报 */
export function seedBroadcastsFromOverload() {
  return loadHotBroadcasts()
}
