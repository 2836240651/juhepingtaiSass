<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Plus, Refresh, View, WarningFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import {
  assignTask,
  cancelAssignedTask,
  fetchAssignedTaskDetail,
  fetchAssignedTasks,
  removeAssignedTask,
  updateAssignedTask,
} from '@/api/assignedTasks'
import { fetchEmployees } from '@/api/employees'
import { fetchWarehouseSites } from '@/api/warehouseSites'
import { fetchWarehouseStaff } from '@/api/warehouseStaff'
import { TASK_STATUS_META } from '@/constants/operations'
import { OUTCOME_MAP } from '@/constants/opsFeedbackDemo'
import {
  ASSIGNEE_TYPE_OPTIONS,
  TASK_DUE_OPTIONS,
  TASK_PLATFORM_OPTIONS,
  TASK_PRIORITY_OPTIONS,
  TASK_STATUS_OPTIONS,
  WAREHOUSE_TASK_CATEGORY_OPTIONS,
  PLATFORM_LABELS,
} from '@/constants/assignedTasks'
import PageHeader from '@/components/common/PageHeader.vue'
import PageScroll from '@/components/common/PageScroll.vue'
import AssignedTaskDetailDrawer from '@/components/tasks/AssignedTaskDetailDrawer.vue'

const auth = useAuthStore()
const loading = ref(false)
const employees = ref([])
const warehouseStaff = ref([])
const warehouseSites = ref([])
const tasks = ref([])
const dialogVisible = ref(false)
const detailVisible = ref(false)
const submitting = ref(false)
const editingId = ref(null)
const filterAssigneeType = ref('all')
const filterAssigneeId = ref('all')
const filterStatus = ref('active')
const activeTask = ref(null)
const activeFeedbacks = ref([])

const priorityMap = Object.fromEntries(TASK_PRIORITY_OPTIONS.map((item) => [item.value, item]))

const activeEmployees = computed(() => employees.value.filter((emp) => emp.status !== false))
const activeWarehouseStaff = computed(() => warehouseStaff.value.filter((item) => item.status !== false))

const assigneeFilterOptions = computed(() => {
  const options = [{ id: 'all', label: '全部负责人', type: 'all' }]
  for (const emp of activeEmployees.value) {
    options.push({ id: emp.id, label: `${emp.name} · ${emp.role}`, type: 'employee' })
  }
  for (const staff of activeWarehouseStaff.value) {
    options.push({ id: staff.id, label: `${staff.name} · 仓库管理员`, type: 'warehouse' })
  }
  return options
})

const filteredTasks = computed(() => {
  let list = tasks.value
  if (filterAssigneeType.value !== 'all') {
    list = list.filter((task) => (task.assigneeType || 'employee') === filterAssigneeType.value)
  }
  if (filterAssigneeId.value !== 'all') {
    list = list.filter((task) => (task.assigneeId || task.employeeId) === filterAssigneeId.value)
  }
  if (filterStatus.value === 'active') {
    list = list.filter((task) => task.status !== '已完成' && task.status !== '已取消')
  } else if (filterStatus.value === 'need_help') {
    list = list.filter((task) => rowNeedsAttention(task))
  } else if (filterStatus.value !== 'all') {
    list = list.filter((task) => task.status === filterStatus.value)
  }
  return list
})

const stats = computed(() => ({
  total: tasks.value.length,
  active: tasks.value.filter((t) => t.status !== '已完成' && t.status !== '已取消').length,
  done: tasks.value.filter((t) => t.status === '已完成').length,
  needHelp: tasks.value.filter((t) => rowNeedsAttention(t)).length,
}))

const form = reactive({
  assigneeType: 'employee',
  assigneeId: '',
  title: '',
  description: '',
  platformKey: 'temu',
  category: '运营',
  priority: 'medium',
  due: '今天 18:00',
  warehouseName: '',
})

const formRules = computed(() => ({
  assigneeId: [{ required: true, message: '请选择负责人', trigger: 'change' }],
  title: [{ required: true, message: '请填写任务标题', trigger: 'blur' }],
  platformKey: form.assigneeType === 'employee'
    ? [{ required: true, message: '请选择平台', trigger: 'change' }]
    : [],
}))

const categoryOptions = computed(() =>
  form.assigneeType === 'warehouse' ? WAREHOUSE_TASK_CATEGORY_OPTIONS : TASK_CATEGORY_OPTIONS,
)

const selectedWarehouseStaff = computed(() =>
  activeWarehouseStaff.value.find((item) => item.id === form.assigneeId),
)

const warehouseNameOptions = computed(() => {
  const staff = selectedWarehouseStaff.value
  if (!staff?.warehouseIds?.length) return []
  const nameMap = Object.fromEntries(warehouseSites.value.map((site) => [site.id, site.name]))
  return staff.warehouseIds.map((id) => nameMap[id] || id)
})

const formRef = ref(null)

const dialogTitle = computed(() => (editingId.value ? '编辑任务' : '分配任务'))

function resetForm() {
  form.assigneeType = 'employee'
  form.assigneeId = activeEmployees.value[0]?.id || activeWarehouseStaff.value[0]?.id || ''
  if (activeEmployees.value[0]?.id) form.assigneeType = 'employee'
  else if (activeWarehouseStaff.value[0]?.id) form.assigneeType = 'warehouse'
  form.title = ''
  form.description = ''
  form.platformKey = 'temu'
  form.category = '运营'
  form.priority = 'medium'
  form.due = '今天 18:00'
  form.warehouseName = ''
  editingId.value = null
  formRef.value?.clearValidate?.()
}

function onAssigneeTypeChange() {
  form.assigneeId = form.assigneeType === 'warehouse'
    ? (activeWarehouseStaff.value[0]?.id || '')
    : (activeEmployees.value[0]?.id || '')
  form.category = form.assigneeType === 'warehouse' ? '出库' : '运营'
  form.warehouseName = warehouseNameOptions.value[0] || ''
}

function openEdit(row) {
  editingId.value = row.id
  form.assigneeType = row.assigneeType || 'employee'
  form.assigneeId = row.assigneeId || row.employeeId
  form.title = row.title
  form.description = row.description || ''
  form.platformKey = row.platformKey
  form.category = row.category
  form.priority = row.priority
  form.due = row.due
  form.warehouseName = row.warehouseName || ''
  dialogVisible.value = true
}

async function openDetail(row) {
  try {
    const res = await fetchAssignedTaskDetail(row.id, auth)
    activeTask.value = res.data.task
    activeFeedbacks.value = res.data.feedbacks
    detailVisible.value = true
  } catch (err) {
    ElMessage.error(err.message || '加载详情失败')
  }
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

function onAssigneeChange(assigneeId) {
  if (form.assigneeType === 'employee') {
    onEmployeeChange(assigneeId)
    return
  }
  form.warehouseName = warehouseNameOptions.value[0] || ''
}

function onEmployeeChange(employeeId) {
  const employee = activeEmployees.value.find((emp) => emp.id === employeeId)
  if (!employee?.platforms?.length) return
  if (!employee.platforms.includes(form.platformKey)) {
    const key = employee.platforms[0]
    form.platformKey = key === 'shopify' || key === 'wordpress' ? 'dtc' : key
  }
}

function latestFeedbackLabel(task) {
  if (!task.lastOutcome) return ''
  return OUTCOME_MAP[task.lastOutcome]?.label || ''
}

function rowNeedsAttention(row) {
  if (row.status === '已完成' || row.status === '已取消') return false
  return row.lastOutcome === 'need_help' || row.lastOutcome === 'blocked'
}

function assigneeTypeLabel(type) {
  return ASSIGNEE_TYPE_OPTIONS.find((item) => item.value === (type || 'employee'))?.label || '运营人员'
}

function platformLabel(row) {
  return PLATFORM_LABELS[row.platformKey] || row.platformKey
}

async function loadData() {
  loading.value = true
  try {
    const [empRes, staffRes, sitesRes, taskRes] = await Promise.all([
      fetchEmployees(auth),
      fetchWarehouseStaff(auth),
      fetchWarehouseSites(auth, { activeOnly: true }),
      fetchAssignedTasks({}, auth),
    ])
    employees.value = empRes.data || []
    warehouseStaff.value = staffRes.data || []
    warehouseSites.value = sitesRes.data || []
    tasks.value = taskRes.data || []
  } catch {
    employees.value = []
    warehouseStaff.value = []
    warehouseSites.value = []
    tasks.value = []
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function submitForm() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    const assignee = form.assigneeType === 'warehouse'
      ? activeWarehouseStaff.value.find((item) => item.id === form.assigneeId)
      : activeEmployees.value.find((item) => item.id === form.assigneeId)
    const payload = {
      assigneeType: form.assigneeType,
      assigneeId: form.assigneeId,
      title: form.title,
      description: form.description,
      platformKey: form.assigneeType === 'warehouse' ? 'warehouse' : form.platformKey,
      category: form.category,
      priority: form.priority,
      due: form.due,
      warehouseName: form.warehouseName,
      assignedBy: '企业管理员',
    }
    if (editingId.value) {
      await updateAssignedTask(editingId.value, {
        assigneeType: form.assigneeType,
        assigneeId: form.assigneeId,
        employeeId: form.assigneeId,
        assignee: assignee?.name,
        title: form.title.trim(),
        description: form.description.trim(),
        platformKey: payload.platformKey,
        category: form.category,
        priority: form.priority,
        due: form.due,
        warehouseName: form.warehouseName,
      }, auth)
      ElMessage.success('任务已更新')
      dialogVisible.value = false
      await loadData()
    } else {
      const res = await assignTask(payload, {
        employees: employees.value,
        warehouseStaff: warehouseStaff.value,
      }, auth)
      ElMessage.success('任务已分配')
      dialogVisible.value = false
      await loadData()
      if (res.data?.id) {
        await openDetail(res.data)
      }
    }
  } catch (err) {
    ElMessage.error(err.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleCancel(row) {
  try {
    await ElMessageBox.confirm(`确定取消任务「${row.title}」？`, '取消任务', { type: 'warning' })
    await cancelAssignedTask(row.id, auth)
    ElMessage.success('任务已取消')
    detailVisible.value = false
    await loadData()
  } catch {
    /* user dismissed */
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除任务「${row.title}」？`, '删除任务', { type: 'warning' })
    await removeAssignedTask(row.id, auth)
    ElMessage.success('任务已删除')
    detailVisible.value = false
    await loadData()
  } catch {
    /* user dismissed */
  }
}

onMounted(loadData)
</script>

<template>
  <PageScroll>
    <template #header>
      <PageHeader title="任务分配" description="向运营人员或仓库管理员指派任务，跟踪反馈进展；分配后可查看任务详情与处理时间线">
        <template #actions>
          <el-button :icon="Refresh" :loading="loading" @click="loadData">刷新</el-button>
          <el-button type="primary" :icon="Plus" @click="openCreate">分配任务</el-button>
        </template>
      </PageHeader>
    </template>

    <div v-loading="loading" class="assign-page">
      <div class="metrics-bar metrics-bar--4">
        <div class="metric-item">
          <div class="metric-value">{{ stats.total }}</div>
          <div class="metric-label">全部分配</div>
        </div>
        <div class="metric-item">
          <div class="metric-value is-warning">{{ stats.active }}</div>
          <div class="metric-label">进行中</div>
        </div>
        <div class="metric-item">
          <div class="metric-value is-danger">{{ stats.needHelp }}</div>
          <div class="metric-label">需协助</div>
        </div>
        <div class="metric-item">
          <div class="metric-value is-success">{{ stats.done }}</div>
          <div class="metric-label">已完成</div>
        </div>
      </div>

      <div class="filter-bar">
        <el-select v-model="filterAssigneeType" placeholder="负责人类型" style="width: 130px" size="small">
          <el-option label="全部类型" value="all" />
          <el-option v-for="item in ASSIGNEE_TYPE_OPTIONS" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filterAssigneeId" placeholder="负责人" style="width: 180px" size="small">
          <el-option label="全部负责人" value="all" />
          <el-option
            v-for="item in assigneeFilterOptions.filter((opt) => opt.id !== 'all')"
            :key="item.id"
            :label="item.label"
            :value="item.id"
          />
        </el-select>
        <el-select v-model="filterStatus" placeholder="状态" style="width: 130px" size="small">
          <el-option label="进行中" value="active" />
          <el-option label="需协助" value="need_help" />
          <el-option label="全部状态" value="all" />
          <el-option v-for="status in TASK_STATUS_OPTIONS" :key="status" :label="status" :value="status" />
        </el-select>
      </div>

      <el-empty v-if="!loading && !filteredTasks.length" description="暂无分配任务" :image-size="88">
        <el-button type="primary" :icon="Plus" @click="openCreate">分配第一个任务</el-button>
      </el-empty>

      <el-table v-else :data="filteredTasks" stripe size="small" class="task-table">
        <el-table-column label="任务" min-width="220">
          <template #default="{ row }">
            <div class="task-title">{{ row.title }}</div>
            <div v-if="row.description" class="task-desc">{{ row.description }}</div>
          </template>
        </el-table-column>
        <el-table-column label="负责人" width="120">
          <template #default="{ row }">
            <div>{{ row.assignee }}</div>
            <div class="task-desc">{{ assigneeTypeLabel(row.assigneeType) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="范围" width="110">
          <template #default="{ row }">
            {{ row.assigneeType === 'warehouse' ? (row.warehouseName || '仓储作业') : platformLabel(row) }}
          </template>
        </el-table-column>
        <el-table-column prop="category" label="类型" width="80" />
        <el-table-column label="优先级" width="72" align="center">
          <template #default="{ row }">
            <el-tag :type="priorityMap[row.priority]?.type || 'info'" size="small">
              {{ priorityMap[row.priority]?.label || '中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最新反馈" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <template v-if="row.lastFeedback">
              <el-tag
                v-if="latestFeedbackLabel(row)"
                size="small"
                :type="OUTCOME_MAP[row.lastOutcome]?.type || 'info'"
                effect="plain"
                style="margin-right: 6px"
              >
                {{ latestFeedbackLabel(row) }}
              </el-tag>
              <span class="feedback-snippet">{{ row.lastFeedback }}</span>
            </template>
            <el-text v-else type="info" size="small">待负责人反馈</el-text>
          </template>
        </el-table-column>
        <el-table-column prop="due" label="截止" width="110" />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-space :size="4">
              <el-tag :type="TASK_STATUS_META[row.status]?.type || 'info'" size="small">
                {{ row.status }}
              </el-tag>
              <el-icon
                v-if="rowNeedsAttention(row)"
                class="need-help-icon"
                color="var(--el-color-warning)"
              >
                <WarningFilled />
              </el-icon>
            </el-space>
          </template>
        </el-table-column>
        <el-table-column prop="assignedAt" label="分配时间" width="150" />
        <el-table-column label="操作" width="190" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" :icon="View" @click="openDetail(row)">
              详情
            </el-button>
            <el-button
              v-if="row.status !== '已完成' && row.status !== '已取消'"
              link
              type="primary"
              size="small"
              @click="openEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="row.status !== '已完成' && row.status !== '已取消'"
              link
              type="warning"
              size="small"
              @click="handleCancel(row)"
            >
              取消
            </el-button>
            <el-button link type="danger" size="small" :icon="Delete" @click="handleDelete(row)" />
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="520px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="88px">
        <el-form-item label="负责人类型">
          <el-radio-group v-model="form.assigneeType" @change="onAssigneeTypeChange">
            <el-radio v-for="item in ASSIGNEE_TYPE_OPTIONS" :key="item.value" :value="item.value">
              {{ item.label }}
            </el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="负责人" prop="assigneeId">
          <el-select
            v-model="form.assigneeId"
            placeholder="选择负责人"
            style="width: 100%"
            @change="onAssigneeChange"
          >
            <template v-if="form.assigneeType === 'warehouse'">
              <el-option
                v-for="staff in activeWarehouseStaff"
                :key="staff.id"
                :label="`${staff.name}（仓库管理员）`"
                :value="staff.id"
              />
            </template>
            <template v-else>
              <el-option
                v-for="emp in activeEmployees"
                :key="emp.id"
                :label="`${emp.name}（${emp.role}）`"
                :value="emp.id"
              />
            </template>
          </el-select>
        </el-form-item>
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="form.title" placeholder="简明描述需完成的事项" maxlength="80" show-word-limit />
        </el-form-item>
        <el-form-item label="任务说明">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="补充背景、要求或验收标准"
          />
        </el-form-item>
        <el-form-item v-if="form.assigneeType === 'employee'" label="关联平台" prop="platformKey">
          <el-select v-model="form.platformKey" style="width: 100%">
            <el-option
              v-for="item in TASK_PLATFORM_OPTIONS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-else label="关联仓库">
          <el-select v-model="form.warehouseName" placeholder="选填，默认不限定" clearable style="width: 100%">
            <el-option v-for="name in warehouseNameOptions" :key="name" :label="name" :value="name" />
          </el-select>
        </el-form-item>
        <el-form-item label="任务类型">
          <el-select v-model="form.category" style="width: 100%">
            <el-option v-for="item in categoryOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-radio-group v-model="form.priority">
            <el-radio v-for="item in TASK_PRIORITY_OPTIONS" :key="item.value" :value="item.value">
              {{ item.label }}
            </el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="截止时间">
          <el-select v-model="form.due" style="width: 100%">
            <el-option v-for="item in TASK_DUE_OPTIONS" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">
          {{ editingId ? '保存' : '确认分配' }}
        </el-button>
      </template>
    </el-dialog>

    <AssignedTaskDetailDrawer
      v-model="detailVisible"
      :task="activeTask"
      :feedbacks="activeFeedbacks"
    />
  </PageScroll>
</template>

<style scoped>
.assign-page {
  display: grid;
  gap: 16px;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.task-table {
  border-radius: var(--ch-radius-lg);
}

.task-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--ch-text);
}

.task-desc {
  margin-top: 4px;
  font-size: 12px;
  color: var(--ch-text-muted);
  line-height: 1.4;
}

.feedback-snippet {
  font-size: 12px;
  color: var(--ch-text-secondary);
}

.need-help-icon {
  font-size: 14px;
}
</style>
