<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  canUseTemuBackend,
  fetchTemuSalesTrend,
  fetchTemuStores,
  loadTemuModuleData,
} from '@/api/temuApi'
import { scopeStoreIds } from '@/utils/scope'
import { useStoreAssignees } from '@/composables/useStoreAssignees'
import { loadHotBroadcasts, seedBroadcastsFromOverload } from '@/utils/temuHotBroadcast'
import PageHeader from '@/components/common/PageHeader.vue'
import PageScroll from '@/components/common/PageScroll.vue'
import TemuOverviewCards from '@/components/temu/TemuOverviewCards.vue'
import TemuBossOverview from '@/components/temu/TemuBossOverview.vue'
import PriceLossTable from '@/components/temu/PriceLossTable.vue'
import SlowMovingPanel from '@/components/temu/SlowMovingPanel.vue'
import HotProductBroadcast from '@/components/temu/HotProductBroadcast.vue'
import RestockPlanner from '@/components/temu/RestockPlanner.vue'
import CompetitorAnalysis from '@/components/temu/CompetitorAnalysis.vue'

const auth = useAuthStore()
const { assigneeMap, loadAssignees, enrichItems } = useStoreAssignees()
const activeTab = ref('profit')
const selectedStoreId = ref('all')
const temuStores = ref([])
const productsRaw = ref([])
const loading = ref(false)
const loadError = ref('')
const hotBroadcasts = ref(loadHotBroadcasts())
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
  if (!useBackendData.value) {
    temuStores.value = []
    return
  }
  try {
    temuStores.value = await fetchTemuStores(auth)
  } catch (err) {
    temuStores.value = []
    loadError.value = err.message || '加载店铺失败'
  }
}

async function loadProducts() {
  if (!useBackendData.value) {
    loadError.value = '请使用后端账号登录，并确保已启动 Java API（:8080）与爬虫入库'
    productsRaw.value = []
    return
  }

  loading.value = true
  loadError.value = ''
  try {
    const result = await loadTemuModuleData({
      auth,
      shopId: selectedStoreId.value,
    })
    productsRaw.value = result.products
    hotBroadcasts.value = seedBroadcastsFromOverload(result.products)
    if (auth.isBoss) {
      salesTrend.value = await fetchTemuSalesTrend({ shopId: selectedStoreId.value })
    }
  } catch (err) {
    productsRaw.value = []
    loadError.value = err.message || '加载 Temu 数据失败'
    ElMessage.warning(loadError.value)
  } finally {
    loading.value = false
  }
}

function onBroadcastsUpdate(list) {
  hotBroadcasts.value = list
}

onMounted(async () => {
  await loadAssignees()
  await loadTemuStores()
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
        </el-space>
      </div>

      <PageHeader
        v-else-if="!temuStores.length && !auth.isBoss"
        title="Temu 运营"
        :description="`${auth.employee.name} · 日常运营与库存管理`"
      />
    </template>

    <el-alert
      v-if="loadError"
      type="warning"
      :closable="false"
      show-icon
      :title="loadError"
      style="margin-bottom: 16px"
    />

    <el-empty
      v-if="!temuStores.length && !loading"
      description="暂无可见的 Temu 店铺"
      :image-size="96"
    >
      <el-text type="info" size="small">
        请先运行 Python 爬虫入库，并用后端账号登录（Boss: admin@crosshub.cn / 12345678）
      </el-text>
    </el-empty>

    <template v-else-if="temuStores.length">
      <div v-loading="loading">
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
              @update:broadcasts="onBroadcastsUpdate"
            />
          </el-tab-pane>

          <el-tab-pane name="restock">
            <template #label>
              <span>备货分析</span>
              <el-badge v-if="alertCount.restock" :value="alertCount.restock" class="tab-badge" />
            </template>
            <RestockPlanner :products="products" :show-store-column="showStoreColumn" />
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
</style>
