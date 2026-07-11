<script setup>
import { computed, ref } from 'vue'
import { TASK_STATUS_META, TASK_STATUS_OPTIONS } from '@/constants/operations'
import { calcTaskStats, groupTasksByAssignee } from '@/utils/operations'

const props = defineProps({
  tasks: { type: Array, default: () => [] },
})

const statusFilter = ref('全部')

const stats = computed(() => calcTaskStats(props.tasks))

const assigneeStats = computed(() =>
  groupTasksByAssignee(props.tasks).sort((a, b) => b.inProgress - a.inProgress),
)

const filteredTasks = computed(() => {
  if (statusFilter.value === '全部') return props.tasks
  return props.tasks.filter((t) => t.status === statusFilter.value)
})

const priorityType = {
  high: 'danger',
  medium: 'warning',
  low: 'info',
}
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <el-space wrap>
        <span>任务完成情况</span>
        <el-tag type="success" effect="plain">完成率 {{ stats.completionRate }}%</el-tag>
      </el-space>
    </template>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :xs="12" :sm="8" :lg="4">
        <div class="stat-block">
          <el-progress type="circle" :width="72" :percentage="stats.completionRate" />
          <el-text size="small" type="info">整体完成率</el-text>
        </div>
      </el-col>
      <el-col :xs="12" :sm="16" :lg="20">
        <el-row :gutter="12">
          <el-col :span="6">
            <el-statistic title="任务总数" :value="stats.total" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="已完成" :value="stats.completed">
              <template #suffix>
                <el-tag type="success" size="small">✓</el-tag>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="进行中" :value="stats.inProgress" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="待处理 / 逾期" :value="stats.pending + stats.overdue">
              <template v-if="stats.overdue" #suffix>
                <el-tag type="danger" size="small">{{ stats.overdue }} 逾期</el-tag>
              </template>
            </el-statistic>
          </el-col>
        </el-row>

        <el-divider content-position="left">员工完成进度</el-divider>
        <el-table :data="assigneeStats" size="small" :show-header="true">
          <el-table-column prop="assignee" label="员工" width="90" />
          <el-table-column label="完成率" width="160">
            <template #default="{ row }">
              <el-progress :percentage="row.rate" :stroke-width="8" />
            </template>
          </el-table-column>
          <el-table-column prop="completed" label="已完成" width="80" align="center" />
          <el-table-column prop="inProgress" label="进行中" width="80" align="center" />
          <el-table-column prop="overdue" label="逾期" width="70" align="center">
            <template #default="{ row }">
              <el-text :type="row.overdue ? 'danger' : 'info'">{{ row.overdue }}</el-text>
            </template>
          </el-table-column>
        </el-table>
      </el-col>
    </el-row>

    <el-divider content-position="left">当前任务清单</el-divider>

    <el-radio-group v-model="statusFilter" size="small" style="margin-bottom: 12px">
      <el-radio-button v-for="opt in TASK_STATUS_OPTIONS" :key="opt" :value="opt">
        {{ opt }}
        <template v-if="opt !== '全部'">
          ({{ props.tasks.filter((t) => t.status === opt).length }})
        </template>
        <template v-else>({{ stats.total }})</template>
      </el-radio-button>
    </el-radio-group>

    <el-table :data="filteredTasks" stripe size="small">
      <el-table-column prop="title" label="任务" min-width="220" show-overflow-tooltip />
      <el-table-column prop="platform" label="平台" width="100" />
      <el-table-column prop="assignee" label="负责人" width="90" />
      <el-table-column prop="category" label="类型" width="80" />
      <el-table-column label="优先级" width="80">
        <template #default="{ row }">
          <el-tag :type="priorityType[row.priority]" size="small">
            {{ row.priority === 'high' ? '高' : row.priority === 'medium' ? '中' : '低' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="进度" width="140">
        <template #default="{ row }">
          <el-progress :percentage="row.progress" :stroke-width="6" />
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="TASK_STATUS_META[row.status]?.type" size="small">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="due" label="截止" width="110" />
      <el-table-column prop="updatedAt" label="更新" width="80" />
    </el-table>
  </el-card>
</template>

<style scoped>
.stat-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
</style>
