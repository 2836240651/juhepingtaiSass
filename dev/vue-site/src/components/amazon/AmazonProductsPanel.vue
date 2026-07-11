<script setup>
import { computed, ref, watch } from 'vue'
import { ACOS_THRESHOLDS } from '@/constants/amazonBoss'
import { summarizeTopProducts, acosMeta, formatAmazonMoney, formatAmazonPercent } from '@/utils/amazonBoss'
import { resolveAmazonProductEmptyHint } from '@/utils/amazonProductHint'
import AmazonPanelHeader from '@/components/amazon/AmazonPanelHeader.vue'
import AssigneeTableColumn from '@/components/common/AssigneeTableColumn.vue'

const props = defineProps({
  products: { type: Array, default: () => [] },
  syncedAt: { type: String, default: '' },
  syncIssue: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  reportsLoading: { type: Boolean, default: false },
  showStoreColumn: { type: Boolean, default: false },
  storeNameMap: { type: Object, default: () => ({}) },
  initialFilter: { type: String, default: 'all' },
})

defineEmits(['refresh', 'refreshReports'])

const filter = ref(props.initialFilter)

const summary = computed(() => summarizeTopProducts(props.products, 20))

const emptyHint = computed(() => {
  if (summary.value.top.length || props.loading) return null
  if (props.syncIssue) return props.syncIssue
  return resolveAmazonProductEmptyHint({ syncedAt: props.syncedAt })
})

const filterOptions = computed(() => [
  { label: 'TOP20 全部', value: 'all' },
  {
    label: summary.value.highAcosCount
      ? `ACOS 偏高 (${summary.value.highAcosCount})`
      : 'ACOS 偏高',
    value: 'high-acos',
  },
  {
    label: summary.value.dangerAcosCount
      ? `ACOS 过高 (${summary.value.dangerAcosCount})`
      : 'ACOS 过高',
    value: 'danger-acos',
  },
])

const filteredProducts = computed(() => {
  let list = summary.value.top
  if (filter.value === 'high-acos') {
    list = list.filter((p) => ['warning', 'danger'].includes(acosMeta(p.acos).level))
  } else if (filter.value === 'danger-acos') {
    list = list.filter((p) => acosMeta(p.acos).level === 'danger')
  }
  return list
})

function profitType(margin) {
  if (margin >= 15) return 'success'
  if (margin >= 8) return 'warning'
  return 'danger'
}

function avgAcosClass(acos) {
  const meta = acosMeta(acos)
  if (meta.level === 'danger') return 'is-danger'
  if (meta.level === 'warning') return 'is-warning'
  return ''
}

watch(
  () => props.initialFilter,
  (value) => {
    if (value === 'products:high-acos') filter.value = 'high-acos'
    else if (value) filter.value = value.replace('products:', '') || 'all'
  },
)
</script>

<template>
  <div class="amz-panel">
    <AmazonPanelHeader
      title="产品 TOP20"
      description="按近 7 日销售额排序，关注 ACOS、转化与库存；Business Report 从卖家后台报表页同步"
      :synced-at="syncedAt"
      secondary-action-label="Business Report 刷新"
      action-label="刷新数据"
      :secondary-loading="reportsLoading"
      :loading="loading"
      @secondary-action="$emit('refreshReports')"
      @action="$emit('refresh')"
    />

    <div class="mini-stats">
      <div class="mini-stat">
        <span class="mini-stat__value">{{ summary.totalRevenueText }}</span>
        <span class="mini-stat__label">TOP20 销售额</span>
      </div>
      <div class="mini-stat">
        <span class="mini-stat__value" :class="avgAcosClass(summary.avgAcos)">
          {{ summary.avgAcos }}%
        </span>
        <span class="mini-stat__label">平均 ACOS</span>
        <el-text size="small" type="info">健康线 ≤ {{ ACOS_THRESHOLDS.good }}%</el-text>
      </div>
      <div class="mini-stat">
        <span class="mini-stat__value is-danger">{{ summary.dangerAcosCount }}</span>
        <span class="mini-stat__label">ACOS 过高</span>
        <el-text size="small" type="info">≥ {{ ACOS_THRESHOLDS.danger }}%</el-text>
      </div>
      <div class="mini-stat">
        <span class="mini-stat__value">{{ summary.totalAdSpendText }}</span>
        <span class="mini-stat__label">广告花费</span>
      </div>
    </div>

    <el-alert
      v-if="emptyHint"
      :type="emptyHint.type || 'warning'"
      :closable="false"
      show-icon
      :title="emptyHint.title"
      :description="emptyHint.description"
      style="margin-bottom: 4px"
    />

    <el-alert
      v-if="!summary.hasAdData && summary.top.length"
      type="info"
      :closable="false"
      show-icon
      title="广告数据尚未同步"
      description="请点击上方「Business Report 刷新」，从卖家后台报表与广告活动页同步 ACOS 与广告花费（需紫鸟与同步助手在线）。"
      style="margin-bottom: 4px"
    />

    <el-alert
      v-if="summary.dangerAcosCount"
      type="error"
      :closable="false"
      show-icon
      title="部分 SKU 广告 ACOS 过高，建议下调竞价或优化关键词"
    />

    <el-segmented v-model="filter" :options="filterOptions" size="small" />

    <el-table :data="filteredProducts" stripe size="small" v-loading="loading" class="product-table">
      <el-table-column label="#" width="48" align="center" fixed="left">
        <template #default="{ row }">{{ row.displayRank }}</template>
      </el-table-column>
      <el-table-column prop="productName" label="商品" min-width="160" show-overflow-tooltip fixed="left" />
      <el-table-column v-if="showStoreColumn" label="店铺" width="130">
        <template #default="{ row }">{{ storeNameMap[row.storeId] || '—' }}</template>
      </el-table-column>
      <AssigneeTableColumn width="90" />
      <el-table-column prop="asin" label="ASIN" width="110" />
      <el-table-column label="7日订单" width="80" align="center">
        <template #default="{ row }">{{ row.orders7d }}</template>
      </el-table-column>
      <el-table-column label="7日销售额" width="128" align="right" class-name="money-col">
        <template #default="{ row }">
          <span class="money-cell">{{ formatAmazonMoney(row.revenue7d, row.currency) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="广告花费" width="118" align="right" class-name="money-col">
        <template #default="{ row }">
          <span class="money-cell">{{ formatAmazonMoney(row.adSpend7d, row.currency) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="ACOS" width="88" align="center" sortable :sort-method="(a, b) => a.acos - b.acos">
        <template #default="{ row }">
          <el-tag v-if="row.acos > 0" :type="acosMeta(row.acos).type" size="small">
            {{ formatAmazonPercent(row.acos) }}
          </el-tag>
          <span v-else class="money-cell">—</span>
        </template>
      </el-table-column>
      <el-table-column label="TACoS" width="72" align="center">
        <template #default="{ row }">{{ formatAmazonPercent(row.tacos) }}</template>
      </el-table-column>
      <el-table-column label="转化率" width="72" align="center">
        <template #default="{ row }">{{ row.conversionRate }}%</template>
      </el-table-column>
      <el-table-column label="会话" width="72" align="center">
        <template #default="{ row }">{{ row.sessions7d }}</template>
      </el-table-column>
      <el-table-column label="FBA库存" width="80" align="center">
        <template #default="{ row }">{{ row.unitsOnHand }}</template>
      </el-table-column>
      <el-table-column label="利润率" width="80" align="center">
        <template #default="{ row }">
          <el-text :type="profitType(row.profitMargin)" size="small">{{ row.profitMargin }}%</el-text>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.amz-panel {
  display: grid;
  gap: 16px;
}

.mini-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

@media (max-width: 960px) {
  .mini-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}

.mini-stat {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 8px;
  background: var(--el-fill-color-lighter);
}

.mini-stat__value {
  font-size: 18px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.money-cell {
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum';
}

.mini-stat__value.is-danger {
  color: var(--el-color-danger);
}

.mini-stat__value.is-warning {
  color: var(--el-color-warning);
}

.mini-stat__label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.product-table :deep(.money-col .cell) {
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum';
  white-space: nowrap;
}

.product-table {
  width: 100%;
}
</style>
