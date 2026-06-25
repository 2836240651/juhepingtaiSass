<script setup>
import { computed } from 'vue'

const props = defineProps({
  labels: { type: Array, default: () => [] },
  values: { type: Array, default: () => [] },
})

const maxValue = computed(() => Math.max(...props.values, 1))

function barHeight(value) {
  return `${Math.round((value / maxValue.value) * 100)}%`
}
</script>

<template>
  <el-card v-if="labels.length" shadow="never" class="trend-card">
    <template #header>近 7 日全店销量趋势</template>
    <div class="trend-chart">
      <div v-for="(label, index) in labels" :key="label" class="trend-bar-wrap">
        <div class="trend-bar" :style="{ height: barHeight(values[index] || 0) }" />
        <span class="trend-value">{{ values[index] || 0 }}</span>
        <span class="trend-label">{{ label }}</span>
      </div>
    </div>
  </el-card>
</template>

<style scoped>
.trend-card {
  margin-bottom: 16px;
}

.trend-chart {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  min-height: 120px;
  padding: 8px 4px 0;
}

.trend-bar-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 0;
}

.trend-bar {
  width: 100%;
  max-width: 36px;
  min-height: 4px;
  background: linear-gradient(180deg, #409eff, #79bbff);
  border-radius: 4px 4px 0 0;
  transition: height 0.3s ease;
}

.trend-value {
  font-size: 12px;
  color: var(--el-text-color-primary);
  font-weight: 600;
}

.trend-label {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}
</style>
