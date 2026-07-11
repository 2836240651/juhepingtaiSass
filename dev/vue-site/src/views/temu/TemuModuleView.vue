<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { usePlatformSyncStore } from '@/stores/platformSync'
import { resolveAppError } from '@/utils/appErrorCode'
import {
  canUseTemuBackend,
  fetchTemuSalesTrend,
  fetchTemuSessionStatus,
  fetchTemuStores,
  loadTemuModuleData,
  refreshTemuDataWithCrawl,
  openTemuSellerLogin,
  pollTemuSessionUntilReady,
  pollTemuProfileIdle,
} from '@/api/temuApi'
import { scopeStoreIds } from '@/utils/scope'
import { useStoreAssignees } from '@/composables/useStoreAssignees'
import { bootstrapHotBroadcasts, loadHotBroadcasts } from '@/api/temuHotBroadcast'
import PageHeader from '@/components/common/PageHeader.vue'
import PageScroll from '@/components/common/PageScroll.vue'
import TemuOverviewCards from '@/components/temu/TemuOverviewCards.vue'
import TemuBossOverview from '@/components/temu/TemuBossOverview.vue'
import PriceLossTable from '@/components/temu/PriceLossTable.vue'
import SlowMovingPanel from '@/components/temu/SlowMovingPanel.vue'
import HotProductBroadcast from '@/components/temu/HotProductBroadcast.vue'
import RestockPlanner from '@/components/temu/RestockPlanner.vue'
import CompetitorAnalysis from '@/components/temu/CompetitorAnalysis.vue'
import TemuLoginGuide from '@/components/temu/TemuLoginGuide.vue'

const auth = useAuthStore()
const syncStore = usePlatformSyncStore()
const { assigneeMap, loadAssignees, enrichItems } = useStoreAssignees()
const activeTab = ref('profit')
const selectedStoreId = ref('all')
const temuStores = ref([])
const productsRaw = ref([])
const loading = ref(false)
const crawling = ref(false)
const crawlHint = ref('')
const loginGuideRef = ref(null)
const syncError = ref(null)
const dataLoadError = ref('')
const hotBroadcasts = ref([])
const salesTrend = ref({ labels: [], values: [] })

const useBackendData = computed(() => canUseTemuBackend(auth))
const scopedStoreIds = computed(() => scopeStoreIds(temuStores.value, auth))

const storeNameMap = computed(() =>
  Object.fromEntries(temuStores.value.map((s) => [s.id, s.storeName])),
)

function withStoreMeta(list) {
  return enrichItems(
    list.map((p) => ({
      ...p,
      storeName: storeNameMap.value[p.storeId] || '未分配店铺',
    })),
  )
}

const products = computed(() => {
  let list = productsRaw.value.filter((p) => scopedStoreIds.value.has(p.storeId))
  if (selectedStoreId.value !== 'all') {
    list = list.filter((p) => p.storeId === selectedStoreId.value)
  }
  return withStoreMeta(list)
})

const overviewProducts = computed(() => {
  if (selectedStoreId.value === 'all') {
    return withStoreMeta(productsRaw.value.filter((p) => scopedStoreIds.value.has(p.storeId)))
  }
  return products.value
})

const overviewStores = computed(() => {
  if (selectedStoreId.value === 'all') return temuStores.value
  return temuStores.value.filter((s) => s.id === selectedStoreId.value)
})

const showStoreList = computed(
  () => selectedStoreId.value === 'all' && temuStores.value.length > 0,
)

const awaitingSync = computed(
  () =>
    useBackendData.value
    && temuStores.value.length > 0
    && !loading.value
    && !crawling.value
    && productsRaw.value.length === 0
    && !syncError.value
    && !dataLoadError.value,
)

const showStoreColumn = computed(() => selectedStoreId.value === 'all')

const alertCount = computed(() => {
  const p = products.value
  return {
    loss: p.filter((i) => i.isLoss).length,
    slow: p.filter((i) => i.slowMoving).length,
    hot: p.filter((i) => i.isHot).length,
    restock: p.filter((i) => i.restock.urgency !== 'normal').length,
  }
})

async function loadTemuStores() {
  try {
    temuStores.value = await fetchTemuStores(auth)
  } catch (err) {
    temuStores.value = []
    dataLoadError.value = err.message || '加载店铺失败'
  }
}

async function loadHotBroadcastFeed(products = []) {
  hotBroadcasts.value = await bootstrapHotBroadcasts(products, auth)
}

async function loadProducts() {
  if (!temuStores.value.length) {
    productsRaw.value = []
    return
  }

  loading.value = true
  dataLoadError.value = ''
  try {
    const result = await loadTemuModuleData({
      auth,
      shopId: selectedStoreId.value,
    })
    productsRaw.value = result.products
    await loadHotBroadcastFeed(result.products)
    if (useBackendData.value && result.products?.length > 0) {
      markSidebarTemuSync({
        status: 'success',
        message: `已加载 ${result.products.length} 条 SKU`,
        rowCount: result.products.length,
        syncedAt: result.meta?.reportTime || '',
      })
    }
    if (auth.isBoss) {
      salesTrend.value = await fetchTemuSalesTrend({
        auth,
        shopId: selectedStoreId.value,
      })
    }
  } catch (err) {
    productsRaw.value = []
    dataLoadError.value = err.message || '加载 Temu 数据失败'
    ElMessage.warning(dataLoadError.value)
  } finally {
    loading.value = false
  }
}

function onBroadcastsUpdate(list) {
  hotBroadcasts.value = list
}

function markSidebarTemuSync({ status, message, rowCount = 0, syncedAt = '' }) {
  const stores = selectedStoreId.value === 'all'
    ? temuStores.value
    : temuStores.value.filter((store) => store.id === selectedStoreId.value)

  for (const store of stores) {
    syncStore.updateStoreStatus({
      platform: 'temu',
      storeId: store.accountId || '',
      storeName: store.storeName,
      externalShopId: store.externalShopId || store.id,
      status,
      message,
      rowCount,
      syncedAt,
    })
  }
}

async function handleRefreshData() {
  if (!useBackendData.value || crawling.value) return

  crawling.value = true
  syncError.value = null
  crawlHint.value = '正在检查 Temu 登录状态...'
  try {
    let session = await fetchTemuSessionStatus()
    await loginGuideRef.value?.reload?.()

    if (!session.ready) {
      if (!session.profile_busy) {
        crawlHint.value = '正在打开 CrossHub 登录窗口...'
        const loginRes = await openTemuSellerLogin()
        if (loginRes.already_open) {
          crawlHint.value = '登录窗口已在运行，请在已弹出的浏览器中完成登录并选择店铺...'
        }
      } else {
        crawlHint.value = '登录窗口已在运行，请在已弹出的浏览器中完成登录并选择店铺...'
      }
      session = await pollTemuSessionUntilReady({ timeoutMs: 300000, intervalMs: 3000 })
      await loginGuideRef.value?.reload?.()
    }

    crawlHint.value = '正在等待登录窗口释放，以便开始同步...'
    await pollTemuProfileIdle({ timeoutMs: 120000, intervalMs: 2000 })
    crawlHint.value = '登录已完成，正在同步销售数据...'
    const res = await refreshTemuDataWithCrawl()
    syncError.value = null
    await loadTemuStores()
    await loadProducts()
    await loginGuideRef.value?.reload?.()
    if (res.conflict) {
      ElMessage.warning('已有同步任务进行中，已等待其完成')
    }
    const rows = res.job?.rows_count
    const reportTime = res.job?.report_time || ''
    markSidebarTemuSync({
      status: 'success',
      message: rows != null ? `已同步 ${rows} 条销售数据` : '已刷新 Temu 数据',
      rowCount: productsRaw.value.length,
      syncedAt: reportTime,
    })
    ElMessage.success(
      rows != null ? `已同步 ${rows} 条销售数据` : '已刷新 Temu 数据',
    )
  } catch (err) {
    syncError.value = resolveAppError(
      { errorCode: err.errorCode, message: err.message },
      auth.tenantId,
    )
    markSidebarTemuSync({
      status: 'failed',
      message: syncError.value.title || err.message || 'Temu 同步失败',
    })
    ElMessage.error(syncError.value.title)
    await loginGuideRef.value?.reload?.()
  } finally {
    crawling.value = false
    crawlHint.value = ''
  }
}

onMounted(async () => {
  await loadAssignees()
  await loadTemuStores()
  await loadHotBroadcastFeed()
  await loadProducts()
})

watch(selectedStoreId, () => {
  loadProducts()
})
</script>

<template>
  <PageScroll>
    <template #header>
      <div v-if="temuStores.length" class="page-toolbar">
        <el-space wrap>
          <el-radio-group v-model="selectedStoreId" size="small">
            <el-radio-button value="all">全部店铺</el-radio-button>
            <el-radio-button
              v-for="store in temuStores"
              :key="store.id"
              :value="store.id"
            >
              {{ store.storeName }}
            </el-radio-button>
          </el-radio-group>
          <el-tag v-if="useBackendData" type="success" size="small">后端实时数据</el-tag>
          <el-button
            v-if="useBackendData"
            type="primary"
            size="small"
            :icon="Refresh"
            :loading="crawling"
            :disabled="crawling"
            @click="handleRefreshData"
          >
            刷新数据
          </el-button>
        </el-space>
      </div>

      <PageHeader
        v-else-if="!temuStores.length && !auth.isBoss"
        title="Temu 运营"
        :description="`${auth.employee.name} · 日常运营与库存管理`"
      />
    </template>

    <el-alert
      v-if="syncError"
      type="warning"
      closable
      show-icon
      style="margin-bottom: 16px"
      :title="syncError.title"
      @close="syncError = null"
    >
      <template #default>
        <p class="sync-alert-text">{{ syncError.summary }}</p>
        <ol v-if="syncError.steps?.length" class="sync-steps">
          <li v-for="(step, index) in syncError.steps" :key="index">{{ step }}</li>
        </ol>
      </template>
    </el-alert>

    <el-alert
      v-if="dataLoadError"
      type="error"
      closable
      show-icon
      style="margin-bottom: 16px"
      :title="dataLoadError"
      @close="dataLoadError = ''"
    />

    <el-alert
      v-if="awaitingSync"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 16px"
      title="店铺已绑定，运营数据待同步"
    >
      <template #default>
        请先按上方黄色提示完成 Temu 卖家后台登录，再点击「刷新数据」同步销量与库存。
      </template>
    </el-alert>

    <el-empty
      v-if="!temuStores.length && !loading"
      description="暂无可见的 Temu 店铺"
      :image-size="96"
    >
      <el-text type="info" size="small">
        Boss 请在「运营绑定」确认 Temu 店铺；员工需被分配 Temu 平台或负责店铺
      </el-text>
    </el-empty>

    <template v-else-if="temuStores.length">
      <TemuLoginGuide v-if="useBackendData" ref="loginGuideRef" />

      <div
        v-loading="loading || crawling"
        :element-loading-text="crawlHint || '加载中...'"
      >
        <TemuBossOverview
          v-if="auth.isBoss"
          :products="overviewProducts"
          :stores="overviewStores"
          :assignee-map="assigneeMap"
          :show-store-list="showStoreList"
          :sales-trend="salesTrend"
          @navigate="activeTab = $event"
        />

        <TemuOverviewCards v-else :products="products" />

        <el-tabs v-model="activeTab" class="temu-tabs">
          <el-tab-pane name="profit">
            <template #label>
              <span>价格亏损</span>
              <el-badge v-if="alertCount.loss" :value="alertCount.loss" class="tab-badge" />
            </template>
            <PriceLossTable :products="products" :show-store-column="showStoreColumn" />
          </el-tab-pane>

          <el-tab-pane name="slow">
            <template #label>
              <span>滞销预警</span>
              <el-badge v-if="alertCount.slow" :value="alertCount.slow" class="tab-badge" />
            </template>
            <SlowMovingPanel :products="products" :show-store-column="showStoreColumn" />
          </el-tab-pane>

          <el-tab-pane name="hot">
            <template #label>
              <span>爆款通报</span>
              <el-badge v-if="alertCount.hot" :value="alertCount.hot" class="tab-badge" />
            </template>
            <HotProductBroadcast
              :products="products"
              :broadcasts="hotBroadcasts"
              :use-backend-data="useBackendData"
              @update:broadcasts="onBroadcastsUpdate"
            />
          </el-tab-pane>

          <el-tab-pane name="restock">
            <template #label>
              <span>备货分析</span>
              <el-badge v-if="alertCount.restock" :value="alertCount.restock" class="tab-badge" />
            </template>
            <RestockPlanner
              :products="products"
              :show-store-column="showStoreColumn"
              :use-backend-data="useBackendData"
            />
          </el-tab-pane>

          <el-tab-pane v-if="auth.isBoss" name="competitor">
            <template #label>
              <span>竞店分析</span>
            </template>
            <CompetitorAnalysis :use-backend-data="useBackendData" />
          </el-tab-pane>
        </el-tabs>
      </div>
    </template>
  </PageScroll>
</template>

<style scoped>
.page-toolbar {
  margin-bottom: 16px;
}

.temu-tabs {
  margin-top: 20px;
}

.tab-badge {
  margin-left: 6px;
  vertical-align: middle;
}

.tab-badge :deep(.el-badge__content) {
  position: relative;
  transform: none;
  vertical-align: middle;
}

.sync-alert-text {
  margin: 0;
  line-height: 1.6;
}

.sync-steps {
  margin: 8px 0 0;
  padding-left: 20px;
  line-height: 1.7;
}

.sync-detail {
  margin-top: 8px;
  border: none;
}

.sync-detail-pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.5;
  color: var(--el-text-color-secondary);
}
</style>
