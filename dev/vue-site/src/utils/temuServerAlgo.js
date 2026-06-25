import { SLOW_MOVING_THRESHOLDS } from '@/constants/temu'
import { productKeyFromRow } from '@/utils/mapReptileSaleToTemuProduct'

function round1(n) {
  return Math.round(n * 10) / 10
}

export function isOnlineListingStatus(status) {
  return String(status) === '300'
}

/** Commander 滞销：已上架且 30 日销量为 0 */
export function isServerSlowMovingRow(row) {
  const s30 = Number(row.son_sales_thirty_days ?? row.sonSalesThirtyDays ?? 0)
  return isOnlineListingStatus(row.status) && s30 === 0
}

/** 用 join_site_time 映射 SaaS 15/30/45 日分级 */
export function buildServerSlowMoving(row) {
  const joinDays = Number(row.join_site_time ?? row.joinSiteTime ?? 0)
  const s15 = Number(row.s15 ?? 0)
  const s10 = Number(row.s10 ?? 0)

  let tierIndex = 0
  if (joinDays >= 45 || (s15 === 0 && s10 === 0 && joinDays >= 30)) {
    tierIndex = 2
  } else if (joinDays >= 30 || s15 === 0) {
    tierIndex = 1
  }

  const tier = SLOW_MOVING_THRESHOLDS[tierIndex]
  const daysWithoutSale = joinDays >= 45 ? joinDays : joinDays >= 30 ? joinDays : Math.max(joinDays, 15)

  return {
    ...tier,
    daysWithoutSale,
    severity: tierIndex + 1,
    alertTitle: tierIndex === 2 ? '严重滞销' : tierIndex === 1 ? '滞销预警' : '动销放缓',
    fromServer: true,
  }
}

export function buildServerRestock(product, inv) {
  const coverDays = Number(inv.cover_days ?? inv.coverDays ?? 0)
  const suggestedRestock = Number(inv.replenish_qty ?? inv.replenishQty ?? 0)
  const warningDays = Number(inv.warning_days ?? inv.warningDays ?? 10)

  let urgency = 'normal'
  let urgencyLabel = '正常'
  if (suggestedRestock > 0) {
    if (coverDays <= warningDays) {
      urgency = 'critical'
      urgencyLabel = '紧急补货'
    } else {
      urgency = 'warning'
      urgencyLabel = '建议补货'
    }
  }

  return {
    ...product.restock,
    avg7DayDaily: product.avg7DayDaily,
    dailyDemand: round1(inv.daily_sales_adj ?? inv.dailySalesAdjusted ?? product.restock?.dailyDemand ?? 0),
    targetStock: Math.ceil(Number(inv.target_stock ?? inv.targetStock ?? 0)),
    suggestedRestock,
    coverDays: round1(coverDays),
    safetyStock: Math.ceil(warningDays),
    stockGap: product.officialStock - Math.ceil(warningDays),
    urgency,
    urgencyLabel,
    isHot: product.isHot,
    canFulfill: false,
    shortfall: suggestedRestock,
    fromServer: true,
  }
}

/**
 * 将 Commander 预警结果合并到已 enrich 的产品列表（以服务端算法为准）
 */
export function applyServerAlgorithms(products, { loseProducts = [], lowWarnings = [], inventoryWarnings = [], overloadProducts = [] } = {}) {
  const loseSet = new Set(loseProducts.map(productKeyFromRow).filter(Boolean))
  const overloadSet = new Set(overloadProducts.map(productKeyFromRow).filter(Boolean))

  const lowMap = new Map()
  for (const row of lowWarnings) {
    const key = productKeyFromRow(row)
    if (key && isServerSlowMovingRow(row)) lowMap.set(key, row)
  }

  const invMap = new Map()
  for (const row of inventoryWarnings) {
    const key = productKeyFromRow(row)
    if (key) invMap.set(key, row)
  }

  return products.map((product) => {
    let next = { ...product }

    if (loseSet.size) {
      next.isLoss = loseSet.has(product.sku)
    }

    const lowRow = lowMap.get(product.sku)
    if (lowMap.size) {
      next.slowMoving = lowRow ? buildServerSlowMoving(lowRow) : null
    }

    const invRow = invMap.get(product.sku)
    if (invRow) {
      next.restock = buildServerRestock(product, invRow)
    } else if (invMap.size) {
      next.restock = { ...product.restock, urgency: 'normal', urgencyLabel: '正常', suggestedRestock: 0, fromServer: true }
    }

    if (overloadSet.has(product.sku)) {
      next.isHot = true
      next.isOverload = true
    }

    return next
  })
}
