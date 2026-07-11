<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { calcTaskStats } from '@/utils/operations'
import { Right } from '@element-plus/icons-vue'

const props = defineProps({
  overview: { type: Object, default: null },
  platformSales: { type: Array, default: () => [] },
  tasks: { type: Array, default: () => [] },
})

const router = useRouter()
const auth = useAuthStore()

const taskStats = computed(() => calcTaskStats(props.tasks))

const totalStores = computed(() => {
  const fromSales = props.platformSales.reduce((sum, row) => sum + (row.storeCount || 0), 0)
  if (fromSales > 0) return fromSales
  return (props.overview?.platforms || []).reduce(
    (sum, platform) => sum + (platform.storeSummaries?.length || 0),
    0,
  )
})

const summaryItems = computed(() => [
  {
    label: '待跟进问题',
    value: props.overview?.totalIssues ?? 0,
    type: props.overview?.totalIssues ? 'danger' : 'success',
    hint: '各平台需今日处理',
  },
  {
    label: '绑定店铺',
    value: totalStores.value,
    hint: `${props.platformSales.length} 个平台`,
  },
  {
    label: '待完成任务',
    value: taskStats.value.total - taskStats.value.completed,
    type: taskStats.value.overdue ? 'danger' : 'warning',
    hint: taskStats.value.overdue ? `${taskStats.value.overdue} 项已逾期` : '运营任务',
  },
  {
    label: '任务完成率',
    value: `${taskStats.value.completionRate}%`,
    type: 'success',
    hint: `${taskStats.value.completed}/${taskStats.value.total} 已完成`,
  },
])

const platformRouteMap = {
  temu: 'temu',
  aliexpress: 'aliexpress',
  walmart: 'walmart',
  pdd: 'pdd',
  douyin: 'douyin',
  channels: 'channels',
  amazon: 'amazon',
  '1688': '1688',
  dtc: 'dtc',
}

function goPlatform(platformId) {
  const segment = platformRouteMap[platformId]
  if (!segment) return
  const prefix = auth.isBoss ? '/boss' : '/employee'
  router.push(`${prefix}/${segment}`)
}

function mergePlatformCard(row) {
  const platform = props.overview?.platforms?.find((p) => p.id === row.id)
  return {
    ...row,
    bound: platform?.bound ?? row.storeCount > 0,
    issueCount: platform?.issueCount ?? row.alerts ?? 0,
  }
}

const platformCards = computed(() => props.platformSales.map(mergePlatformCard))
</script>

<template>
  <div class="ops-summary">
    <div class="summary-bar">
      <div
        v-for="item in summaryItems"
        :key="item.label"
        class="summary-item"
      >
        <div class="summary-value" :class="item.type ? `is-${item.type}` : ''">
          {{ item.value }}
        </div>
        <div class="summary-label">{{ item.label }}</div>
        <div class="summary-hint">{{ item.hint }}</div>
      </div>
    </div>

    <div v-if="platformCards.length" class="platform-cards">
      <button
        v-for="card in platformCards"
        :key="card.id"
        type="button"
        class="platform-card"
        @click="goPlatform(card.id)"
      >
        <div class="platform-card__top">
          <strong>{{ card.name }}</strong>
          <el-tag
            :type="card.issueCount ? 'danger' : 'success'"
            size="small"
            effect="plain"
          >
            {{ card.issueCount ? `${card.issueCount} 待跟进` : '正常' }}
          </el-tag>
        </div>
        <div class="platform-card__owner">负责人 · {{ card.owner }}</div>
        <div class="platform-card__metrics">
          <span>{{ card.revenueText }}</span>
          <span class="dot">·</span>
          <span>{{ card.orders }} 单</span>
          <span class="dot">·</span>
          <span>{{ card.storeCount }} 店</span>
        </div>
        <div class="platform-card__action">
          进入运营 <el-icon><Right /></el-icon>
        </div>
      </button>
    </div>

    <el-empty
      v-else
      description="暂无绑定店铺，请先在账户绑定中配置"
      :image-size="72"
    />
  </div>
</template>

<style scoped>
.ops-summary {
  display: grid;
  gap: 16px;
}
</style>
