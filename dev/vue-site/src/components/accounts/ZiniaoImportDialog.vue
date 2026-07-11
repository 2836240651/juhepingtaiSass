<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchAmazonIntegrationStatus } from '@/api/agentApi'
import { probeLocalZiniao } from '@/utils/ziniaoProbe'
import { probeLocalAgent } from '@/utils/agentProbe'
import {
  bindZiniaoStores,
  discoverZiniaoStoresWithPoll,
  fetchZiniaoCandidates,
} from '@/api/amazonIntegrationApi'
import { formatCaughtError } from '@/utils/appErrorCode'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'bound'])

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const router = useRouter()
const loadingStatus = ref(false)
const discovering = ref(false)
const binding = ref(false)
const integrationStatus = ref({})
const localZiniaoOnline = ref(false)
const localAgentOnline = ref(false)
const candidates = ref([])
const selectedIds = ref([])
const tableRef = ref(null)

const agentOnline = computed(
  () => localAgentOnline.value || Boolean(integrationStatus.value.agent_online),
)
const ziniaoOnline = computed(() => localZiniaoOnline.value || Boolean(integrationStatus.value.ziniao_online))

const selectableCandidates = computed(() =>
  candidates.value.filter((item) => item.browserId),
)

async function loadStatus() {
  loadingStatus.value = true
  try {
    const [res, ziniaoReady, agentReady] = await Promise.all([
      fetchAmazonIntegrationStatus(),
      probeLocalZiniao(),
      probeLocalAgent(),
    ])
    integrationStatus.value = res.data || {}
    localZiniaoOnline.value = ziniaoReady
    localAgentOnline.value = agentReady
  } catch (err) {
    integrationStatus.value = {}
    localZiniaoOnline.value = false
    localAgentOnline.value = false
    ElMessage.error(formatCaughtError(err, '无法获取 Agent 状态'))
  } finally {
    loadingStatus.value = false
  }
}

async function loadCandidates() {
  const res = await fetchZiniaoCandidates()
  candidates.value = res.data || []
  selectedIds.value = candidates.value.map((item) => item.browserId)
  await nextTick()
  syncTableSelection()
}

function syncTableSelection() {
  const table = tableRef.value
  if (!table) return
  table.clearSelection()
  for (const row of selectableCandidates.value) {
    if (selectedIds.value.includes(row.browserId)) {
      table.toggleRowSelection(row, true)
    }
  }
}

function onSelectionChange(rows) {
  selectedIds.value = (rows || []).map((row) => row.browserId)
}

function goAgentSetup() {
  visible.value = false
  router.push('/boss/agent-nodes')
}

async function runDiscover() {
  discovering.value = true
  try {
    const result = await discoverZiniaoStoresWithPoll()
    candidates.value = result.stores || []
    selectedIds.value = candidates.value.map((item) => item.browserId)
    if (!candidates.value.length) {
      ElMessage.warning('未发现可绑定的紫鸟店铺')
    } else {
      ElMessage.success(`发现 ${candidates.value.length} 个紫鸟店铺`)
      await nextTick()
      syncTableSelection()
    }
  } catch (err) {
    ElMessage.error(formatCaughtError(err, '扫描紫鸟店铺失败'))
  } finally {
    discovering.value = false
  }
}

async function confirmBind() {
  const selected = selectableCandidates.value.filter((item) =>
    selectedIds.value.includes(item.browserId),
  )
  if (!selected.length) {
    ElMessage.warning('请至少选择一个店铺')
    return
  }
  binding.value = true
  try {
    await bindZiniaoStores(selected)
    ElMessage.success(`已绑定 ${selected.length} 个 Amazon 店铺`)
    visible.value = false
    emit('bound')
  } catch (err) {
    ElMessage.error(formatCaughtError(err, '绑定失败'))
  } finally {
    binding.value = false
  }
}

watch(
  () => props.modelValue,
  async (open) => {
    if (!open) return
    await loadStatus()
    try {
      await loadCandidates()
    } catch {
      candidates.value = []
    }
  },
)
</script>

<template>
  <el-dialog
    v-model="visible"
    title="从紫鸟导入 Amazon 店铺"
    width="720px"
    destroy-on-close
  >
    <div v-loading="loadingStatus" class="ziniao-import">
      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="需在本机启动紫鸟与 Amazon 同步助手"
        description="请到「设置 → Amazon 同步助手」下载两个启动文件，双击运行后保持同步助手窗口打开。"
      />

      <div class="status-row">
        <el-tag :type="agentOnline ? 'success' : 'danger'" effect="plain">
          同步助手 {{ agentOnline ? '在线' : '离线' }}
        </el-tag>
        <el-tag :type="ziniaoOnline ? 'success' : 'warning'" effect="plain">
          紫鸟 {{ ziniaoOnline ? '已就绪' : '未就绪' }}
        </el-tag>
        <el-button link type="primary" @click="loadStatus">刷新状态</el-button>
        <el-button v-if="!agentOnline || !ziniaoOnline" link type="primary" @click="goAgentSetup">
          去下载助手
        </el-button>
      </div>

      <div class="actions-row">
        <el-button type="primary" :loading="discovering" @click="runDiscover">
          扫描紫鸟店铺
        </el-button>
      </div>

      <el-table
        v-if="selectableCandidates.length"
        ref="tableRef"
        :data="selectableCandidates"
        size="small"
        stripe
        row-key="browserId"
        @selection-change="onSelectionChange"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column prop="browserName" label="紫鸟店铺名" min-width="160" />
        <el-table-column prop="platformName" label="平台" width="140" />
        <el-table-column prop="storeUsername" label="登录账号" min-width="160" show-overflow-tooltip />
        <el-table-column prop="browserIp" label="IP" width="130" />
      </el-table>

      <el-empty v-else description="暂无候选店铺，请先扫描" :image-size="72" />
    </div>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="binding" :disabled="!selectedIds.length" @click="confirmBind">
        绑定所选
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.ziniao-import {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-row,
.actions-row,
.register-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.agent-link {
  font-size: 13px;
  margin-left: 4px;
}
</style>
