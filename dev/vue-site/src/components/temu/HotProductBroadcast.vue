<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { formatPercent } from '@/utils/format'
import { RESTOCK_CONFIG } from '@/constants/temu'
import { appendHotBroadcast } from '@/utils/temuHotBroadcast'

const props = defineProps({
  products: { type: Array, required: true },
  broadcasts: { type: Array, default: () => [] },
})

const emit = defineEmits(['broadcast', 'update:broadcasts'])

const localBroadcasts = ref([...props.broadcasts])

watch(
  () => props.broadcasts,
  (next) => {
    localBroadcasts.value = [...next]
  },
)

const hotProducts = computed(() =>
  [...props.products]
    .filter((p) => p.dailySales > 0)
    .sort((a, b) => b.surgeRatio - a.surgeRatio),
)

function surgeTagType(ratio) {
  if (ratio >= RESTOCK_CONFIG.hotSurgeRatio) return 'danger'
  if (ratio >= 1.2) return 'warning'
  return 'info'
}

function sendBroadcast(product) {
  const entry = {
    id: Date.now(),
    time: new Date().toLocaleString('zh-CN', { hour12: false }),
    sku: product.sku,
    name: product.name,
    dailySales: product.dailySales,
    avg7DayDaily: product.avg7DayDaily,
    surgeRatio: product.surgeRatio,
    operator: '系统',
    readBy: [],
  }
  localBroadcasts.value = appendHotBroadcast(entry)
  emit('broadcast', entry)
  emit('update:broadcasts', localBroadcasts.value)
  ElMessage.success(`已全公司通报：${product.name}`)
}
</script>

<template>
  <div>
    <el-row :gutter="16">
      <el-col :xs="24" :lg="14">
        <el-card shadow="never">
          <template #header>
            <span>爆款识别（当日销量 vs 7 日均值）</span>
          </template>

          <el-table :data="hotProducts" stripe>
            <el-table-column prop="sku" label="SKU" width="110" />
            <el-table-column prop="name" label="商品名称" min-width="160" show-overflow-tooltip />
            <el-table-column label="当日销量" width="100" align="right" prop="dailySales" sortable />
            <el-table-column label="7 日均值" width="100" align="right">
              <template #default="{ row }">{{ row.avg7DayDaily }}</template>
            </el-table-column>
            <el-table-column label="增幅" width="100" align="right" sortable prop="surgeRatio">
              <template #default="{ row }">
                <el-tag :type="surgeTagType(row.surgeRatio)" size="small">
                  {{ formatPercent((row.surgeRatio - 1) * 100) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="判定" width="90">
              <template #default="{ row }">
                <el-tag v-if="row.isHot" type="danger" effect="dark">爆款</el-tag>
                <el-tag v-else type="info" effect="plain">正常</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="110" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" :disabled="!row.isHot" @click="sendBroadcast(row)">
                  通报
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card shadow="never">
          <template #header>
            <el-space>
              <span>全公司通报记录</span>
              <el-tag size="small">{{ localBroadcasts.length }} 条</el-tag>
            </el-space>
          </template>

          <el-empty v-if="!localBroadcasts.length" description="暂无通报记录" :image-size="64" />

          <el-timeline v-else>
            <el-timeline-item
              v-for="item in localBroadcasts"
              :key="item.id"
              :timestamp="item.time"
              type="success"
            >
              <strong>{{ item.name }}</strong>
              <el-text tag="p" size="small" type="info">
                当日 {{ item.dailySales }} 件 · 7 日均 {{ item.avg7DayDaily }} · 增幅 {{ formatPercent((item.surgeRatio - 1) * 100) }}
              </el-text>
              <el-text v-if="item.readBy?.length" size="small" type="success">
                已读：{{ item.readBy.join('、') }}
              </el-text>
            </el-timeline-item>
          </el-timeline>
        </el-card>

        <el-card shadow="never" style="margin-top: 16px">
          <template #header>爆款判定规则</template>
          <el-descriptions :column="1" size="small" border>
            <el-descriptions-item label="当日销量">≥ {{ RESTOCK_CONFIG.hotMinDailySales }} 件</el-descriptions-item>
            <el-descriptions-item label="增幅阈值">当日 / 7 日均 ≥ {{ RESTOCK_CONFIG.hotSurgeRatio }}×</el-descriptions-item>
            <el-descriptions-item label="通报范围">全公司员工可见（localStorage 持久化）</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
