import { formatMoneyDecimal } from '@/utils/format'

export function summarizeAliExpressOrders(orders = []) {
  const jit = orders.filter((o) => o.fulfillmentType === 'jit')
  const warehouse = orders.filter((o) => o.fulfillmentType === 'warehouse')
  const jitPending = jit.filter((o) => ['待发货', '待揽收'].includes(o.status)).length
  const warehousePending = warehouse.filter((o) => o.status === '待出库').length
  const totalAmount = orders.reduce((sum, o) => sum + (o.amount || 0), 0)

  return {
    total: orders.length,
    jitTotal: jit.length,
    warehouseTotal: warehouse.length,
    pending: jitPending + warehousePending,
    jitPending,
    warehousePending,
    totalAmount,
    totalAmountText: totalAmount > 0 ? `$${formatMoneyDecimal(totalAmount)}` : '—',
  }
}

export function summarizeAliExpressViolations(violations = []) {
  const pending = violations.filter((v) => !v.confirmed).length
  const appealed = violations.filter((v) => v.appealStatus === 'appealed').length
  const notAppealed = violations.filter((v) => v.appealStatus === 'not_appealed').length
  const appealPending = violations.filter((v) => v.appealResult === 'pending').length
  const appealSuccess = violations.filter((v) => v.appealResult === 'success').length
  const appealFailed = violations.filter((v) => v.appealResult === 'failed').length
  const totalFine = violations.reduce((sum, v) => sum + (v.fineAmount || 0), 0)

  let healthScore = 100
  healthScore -= pending * 8
  healthScore -= appealPending * 4
  healthScore -= appealFailed * 6
  healthScore = Math.max(0, Math.min(100, healthScore))

  let healthType = 'success'
  let healthLabel = '良好'
  if (healthScore < 60) {
    healthType = 'danger'
    healthLabel = '需关注'
  } else if (healthScore < 85) {
    healthType = 'warning'
    healthLabel = '一般'
  }

  return {
    total: violations.length,
    pending,
    appealed,
    notAppealed,
    appealPending,
    appealSuccess,
    appealFailed,
    totalFine,
    totalFineText: `$${formatMoneyDecimal(totalFine)}`,
    healthScore,
    healthType,
    healthLabel,
  }
}

export function summarizeAliExpressProducts(products = []) {
  const hot = products.filter((p) => p.isHot).length
  return {
    skuCount: products.length,
    hotCount: hot,
  }
}

export function summarizeAliExpressByStore(orders, violations, products, stores = []) {
  return stores.map((store) => {
    const storeOrders = orders.filter((o) => o.storeId === store.id)
    const storeViolations = violations.filter((v) => v.storeId === store.id)
    const storeProducts = products.filter((p) => p.storeId === store.id)
    return {
      store,
      orders: summarizeAliExpressOrders(storeOrders),
      violations: summarizeAliExpressViolations(storeViolations),
      products: summarizeAliExpressProducts(storeProducts),
    }
  })
}
