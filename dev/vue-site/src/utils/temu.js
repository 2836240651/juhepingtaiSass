import { RESTOCK_CONFIG, SLOW_MOVING_THRESHOLDS, LISTING_STATUS } from '@/constants/temu'
import { TEMU_PLATFORM_IDS } from '@/constants/temuOps'

/** 计算单件利润与是否亏损 */
export function calcProfit(product) {
  const platformFee = product.sellingPrice * product.platformFeeRate
  const unitProfit = product.sellingPrice - product.costPrice - platformFee - product.logisticsFee
  const profitRate = product.sellingPrice > 0 ? (unitProfit / product.sellingPrice) * 100 : 0
  return {
    platformFee: round2(platformFee),
    unitProfit: round2(unitProfit),
    profitRate: round2(profitRate),
    isLoss: unitProfit < 0,
  }
}

/** 7 日日均销量 */
export function calcAvg7DayDaily(salesLast7Days) {
  if (!salesLast7Days?.length) return 0
  const total = salesLast7Days.reduce((s, n) => s + n, 0)
  return round1(total / salesLast7Days.length)
}

/** 当日 vs 7 日均值增幅 */
export function calcSurgeRatio(dailySales, avg7DayDaily) {
  if (avg7DayDaily <= 0) return dailySales > 0 ? 999 : 0
  return round2(dailySales / avg7DayDaily)
}

/** 是否判定为爆款（当日销量显著高于 7 日均值） */
export function isHotProduct(dailySales, avg7DayDaily, config = RESTOCK_CONFIG) {
  const ratio = calcSurgeRatio(dailySales, avg7DayDaily)
  return dailySales >= config.hotMinDailySales && ratio >= config.hotSurgeRatio
}

/** 滞销分级 */
export function getSlowMovingTier(daysWithoutSale) {
  if (daysWithoutSale >= 45) {
    return { ...SLOW_MOVING_THRESHOLDS[2], daysWithoutSale, severity: 3, alertTitle: '严重滞销' }
  }
  if (daysWithoutSale >= 30) {
    return { ...SLOW_MOVING_THRESHOLDS[1], daysWithoutSale, severity: 2, alertTitle: '滞销预警' }
  }
  if (daysWithoutSale >= 15) {
    return { ...SLOW_MOVING_THRESHOLDS[0], daysWithoutSale, severity: 1, alertTitle: '动销放缓' }
  }
  return null
}

/** 官方仓可售天数 */
export function calcCoverDays(officialStock, dailyDemand) {
  if (dailyDemand <= 0) return officialStock > 0 ? 999 : 0
  return round1(officialStock / dailyDemand)
}

/**
 * 备货建议：本地仓 → Temu 官方仓
 * 目标库存 = 日均需求 × (目标覆盖天数 + 备货提前期)
 * 建议补货 = max(0, 目标库存 - 官方仓现有)，且不超过本地仓可用
 */
export function calcRestockPlan(product, config = RESTOCK_CONFIG) {
  const avg7DayDaily = calcAvg7DayDaily(product.salesLast7Days)
  const dailyDemand = Math.max(product.dailySales, avg7DayDaily)
  const targetStock = Math.ceil(dailyDemand * (config.targetCoverDays + config.leadTimeDays))
  const rawSuggest = Math.max(0, targetStock - product.officialStock)
  const suggestedRestock = Math.min(rawSuggest, product.localStock)
  const coverDays = calcCoverDays(product.officialStock, dailyDemand)
  const safetyStock = Math.ceil(dailyDemand * config.safetyDays)
  const stockGap = product.officialStock - safetyStock

  let urgency = 'normal'
  let urgencyLabel = '正常'
  if (coverDays <= config.leadTimeDays) {
    urgency = 'critical'
    urgencyLabel = '紧急补货'
  } else if (coverDays <= config.safetyDays) {
    urgency = 'warning'
    urgencyLabel = '建议补货'
  } else if (stockGap < 0) {
    urgency = 'caution'
    urgencyLabel = '低于安全线'
  }

  const isHot = isHotProduct(product.dailySales, avg7DayDaily, config)

  return {
    avg7DayDaily,
    dailyDemand: round1(dailyDemand),
    targetStock,
    suggestedRestock,
    coverDays,
    safetyStock,
    stockGap,
    urgency,
    urgencyLabel,
    isHot,
    canFulfill: product.localStock >= rawSuggest,
    shortfall: Math.max(0, rawSuggest - product.localStock),
  }
}

/**  enrich 单条 SKU */
export function enrichTemuProduct(raw) {
  const profit = calcProfit(raw)
  const avg7DayDaily = calcAvg7DayDaily(raw.salesLast7Days)
  const surgeRatio = calcSurgeRatio(raw.dailySales, avg7DayDaily)
  const slowMoving = getSlowMovingTier(raw.daysWithoutSale)
  const restock = calcRestockPlan(raw)
  const hot = isHotProduct(raw.dailySales, avg7DayDaily)
  const listingStatus = raw.listingStatus === 'offline' ? 'offline' : 'online'
  const listingMeta = LISTING_STATUS[listingStatus]
  const platformIds = raw.spuId
    ? { spuId: raw.spuId, skcId: raw.skcId || '', skuId: raw.skuId || '' }
    : (TEMU_PLATFORM_IDS[raw.sku] || {})

  return {
    ...raw,
    ...profit,
    ...platformIds,
    avg7DayDaily,
    surgeRatio,
    slowMoving,
    restock,
    isHot: hot,
    surgePercent: round1((surgeRatio - 1) * 100),
    listingStatus,
    isOnline: listingStatus === 'online',
    listingStatusLabel: listingMeta.label,
    listingStatusType: listingMeta.type,
  }
}

export function enrichAllProducts(rawList) {
  return rawList.map(enrichTemuProduct)
}

function round1(n) {
  return Math.round(n * 10) / 10
}

function round2(n) {
  return Math.round(n * 100) / 100
}
