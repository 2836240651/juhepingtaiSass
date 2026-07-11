import { DOMESTIC_PENDING_STATUSES } from '@/constants/domesticShared'
import { formatMoney, formatMoneyDecimal } from '@/utils/format'
import { attachAssignee, buildStoreAssigneeMap, resolveStoreAssignee } from '@/utils/storeAssignment'

function withStoreName(item, storeNameMap) {
  return {
    ...item,
    storeName: storeNameMap[item.storeId] || item.storeName || '—',
  }
}

function mapStoreSummaries(stores, assigneeMap) {
  return stores.map((store) => ({
    storeId: store.id,
    storeName: store.storeName,
    assigneeName: resolveStoreAssignee(store.id, assigneeMap),
  }))
}

export function summarizeDomesticOrders(orders = []) {
  const pending = orders.filter((o) => DOMESTIC_PENDING_STATUSES.has(o.status)).length
  const totalAmount = orders.reduce((sum, o) => sum + (o.amount || 0), 0)

  return {
    total: orders.length,
    pending,
    shipped: orders.filter((o) => o.status === '已发货').length,
    totalAmount,
    totalAmountText: formatMoney(totalAmount),
  }
}

export function summarizeDomesticIssues(issues = []) {
  const openItems = issues.filter((item) => !item.resolved)
  const high = openItems.filter((item) => item.severity === 'high').length
  return {
    total: issues.length,
    open: openItems.length,
    high,
    resolved: issues.filter((item) => item.resolved).length,
  }
}

export function summarizeDomesticByStore(orders, issues, stores = []) {
  return stores.map((store) => {
    const storeOrders = orders.filter((o) => o.storeId === store.id)
    const storeIssues = issues.filter((i) => i.storeId === store.id)
    return {
      store,
      orders: summarizeDomesticOrders(storeOrders),
      issues: summarizeDomesticIssues(storeIssues),
    }
  })
}

export function enrichDomesticIssue(issue, issueTypeMap = {}) {
  const meta = issueTypeMap[issue.type] || { label: issue.type, type: 'info' }
  return {
    ...issue,
    typeLabel: meta.label,
    typeTag: meta.type,
  }
}

export function formatDomesticAmount(amount, currency = 'CNY') {
  return `${formatMoneyDecimal(amount)} ${currency}`
}

export function buildDomesticPlatformSection(config, payload, storeNameMap, assigneeMap) {
  const { id, name, route, issueTypeMap } = config
  const { stores = [], orders = [], issues = [] } = payload

  const mapOrder = (o, extra) =>
    attachAssignee(
      withStoreName(
        {
          storeId: o.storeId,
          orderNo: o.orderNo,
          productName: o.productName,
          sku: o.sku,
          channel: o.channel,
          status: o.status,
          shipDeadline: o.shipDeadline,
          ...extra,
        },
        storeNameMap,
      ),
      o.storeId,
      assigneeMap,
    )

  const pendingOrders = orders
    .filter((o) => DOMESTIC_PENDING_STATUSES.has(o.status))
    .map((o) => mapOrder(o, { isShipped: false }))

  const shippedOrders = orders
    .filter((o) => o.status === '已发货')
    .map((o) => mapOrder(o, { isShipped: true }))

  const openIssues = issues
    .filter((item) => !item.resolved)
    .map((item) =>
      attachAssignee(
        withStoreName(
          {
            storeId: item.storeId,
            id: item.id,
            typeLabel: item.typeLabel || item.type,
            sku: item.sku,
            productName: item.productName,
            detail: item.detail,
            severity: item.severity,
            isResolved: item.resolved,
          },
          storeNameMap,
        ),
        item.storeId,
        assigneeMap,
      ),
    )

  const storeSummaries = mapStoreSummaries(stores, assigneeMap)

  const storeGroups = storeSummaries.map((summary) => {
    const sid = summary.storeId
    const storePending = pendingOrders.filter((item) => item.storeId === sid)
    const storeShipped = shippedOrders.filter((item) => item.storeId === sid)
    const storeIssueItems = openIssues.filter((item) => item.storeId === sid)
    return {
      ...summary,
      issueCount: storePending.length + storeIssueItems.length,
      pendingOrders: storePending,
      shippedOrders: storeShipped,
      openIssues: storeIssueItems,
    }
  })

  return {
    id,
    name,
    bound: (stores?.length || 0) > 0,
    issueCount: pendingOrders.length + openIssues.length,
    storeSummaries,
    storeGroups,
    pendingOrders,
    shippedOrders,
    pendingOrderCount: pendingOrders.length,
    shippedOrderCount: shippedOrders.length,
    openIssues,
    openIssueCount: openIssues.length,
    issueTypeMap,
    route,
  }
}
