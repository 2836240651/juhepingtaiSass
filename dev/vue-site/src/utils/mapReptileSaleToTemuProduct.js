/** 分 → 元 */
export function centsToYuan(value) {
  const n = Number(value)
  if (Number.isNaN(n)) return 0
  return Math.round(n) / 100
}

/** Commander status → SaaS listingStatus */
export function statusToListing(status) {
  return String(status) === '400' ? 'offline' : 'online'
}

/** 由 7 日总销量估算每日序列（Commander 仅存总量） */
export function salesLast7DaysFromRow(row) {
  const total7 = Number(row.son_sales_seven_days ?? row.sonSalesSevenDays ?? 0)
  const daily = Math.round(total7 / 7)
  return Array.from({ length: 7 }, () => daily)
}

/** 无 Commander 滞销明细时，用 join_site_time 与销量粗估 */
export function estimateDaysWithoutSale(row) {
  const s30 = Number(row.son_sales_thirty_days ?? row.sonSalesThirtyDays ?? 0)
  const s7 = Number(row.son_sales_seven_days ?? row.sonSalesSevenDays ?? 0)
  const today = Number(row.son_today_sales ?? row.sonTodaySales ?? 0)
  const joinDays = Number(row.join_site_time ?? row.joinSiteTime ?? 0)

  if (s30 === 0 && today === 0) {
    if (joinDays >= 45) return 45
    if (joinDays >= 30) return 30
    if (joinDays >= 15) return 15
    return joinDays || 15
  }
  if (today === 0 && s7 === 0) return 15
  return 0
}

/**
 * 将 commander TableReptileSale 行映射为 enrichTemuProduct 输入结构
 * @param {Record<string, unknown>} row
 * @param {Record<string, unknown>} [overrides]
 */
export function mapReptileSaleToTemuProduct(row, overrides = {}) {
  const sku = String(row.ext_code ?? row.extCode ?? row.son_ext_code ?? '').trim()
  const sellingPrice = centsToYuan(row.son_price ?? row.sonPrice)
  const costPrice = centsToYuan(row.cost ?? 0)

  return {
    sku,
    storeId: String(row.shop_id ?? row.shopId ?? ''),
    name: String(row.title ?? sku),
    sellingPrice,
    costPrice,
    platformFeeRate: 0.15,
    logisticsFee: 0,
    officialStock: Number(row.warehouse_available_stock ?? row.warehouseAvailableStock ?? 0),
    localStock: 0,
    daysWithoutSale: estimateDaysWithoutSale(row),
    dailySales: Number(row.son_today_sales ?? row.sonTodaySales ?? 0),
    salesLast7Days: salesLast7DaysFromRow(row),
    category: String(row.category_name ?? row.categoryName ?? ''),
    owner: String(row.nickname ?? row.username ?? overrides.owner ?? ''),
    listingStatus: statusToListing(row.status),
    spuId: String(row.spu ?? ''),
    skcId: String(row.skc ?? ''),
    skuId: String(row.son_sku ?? row.sonSku ?? ''),
    imgUrl: String(row.img_url ?? row.imgUrl ?? ''),
    ...overrides,
  }
}

export function productKeyFromRow(row) {
  return String(row.ext_code ?? row.extCode ?? row.son_ext_code ?? '').trim()
}
