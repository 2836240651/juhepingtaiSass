<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchAmazonIntegrationStatus } from '@/api/agentApi'
import { probeLocalZiniao } from '@/utils/ziniaoProbe'
import { probeLocalAgent } from '@/utils/agentProbe'

const props = defineProps({
  compact: { type: Boolean, default: false },
})

const router = useRouter()
const loading = ref(false)
const status = ref({})
const localZiniaoOnline = ref(false)
const localAgentOnline = ref(false)

const agentOnline = computed(
  () => localAgentOnline.value || Boolean(status.value.agent_online),
)
const ziniaoOnline = computed(() => localZiniaoOnline.value || Boolean(status.value.ziniao_online))
const allReady = computed(() => agentOnline.value && ziniaoOnline.value)

async function loadStatus() {
  loading.value = true
  try {
    const [res, ziniaoReady, agentReady] = await Promise.all([
      fetchAmazonIntegrationStatus(),
      probeLocalZiniao(),
      probeLocalAgent(),
    ])
    status.value = res.data || {}
    localZiniaoOnline.value = ziniaoReady
    localAgentOnline.value = agentReady
  } catch {
    status.value = {}
    localZiniaoOnline.value = false
  } finally {
    loading.value = false
  }
}

function goAgentSettings() {
  router.push('/boss/agent-nodes')
}

function goAccountBinding() {
  router.push('/boss/accounts')
}

onMounted(loadStatus)

defineExpose({ reload: loadStatus, allReady })
</script>

<template>
  <el-alert
    v-if="!loading && !allReady"
    :type="agentOnline ? 'warning' : 'error'"
    show-icon
    :closable="false"
    class="amazon-integration-guide"
    :class="{ 'is-compact': compact }"
  >
    <template #title>
      {{ agentOnline ? '紫鸟未就绪' : 'Amazon 同步助手未运行' }}
    </template>
    <template #default>
      <ol class="guide-steps">
        <li>打开 <el-link type="primary" @click="goAgentSettings">设置 → Amazon 同步助手</el-link></li>
        <li>下载并运行「紫鸟启动助手」</li>
        <li>下载并运行「Amazon 同步助手」，<strong>保持窗口不要关闭</strong></li>
        <li>回到 <el-link type="primary" @click="goAccountBinding">账户绑定</el-link> 从紫鸟导入店铺</li>
      </ol>
      <p class="guide-note">全程在网页下载启动文件即可，无需修改代码或配置文件。</p>
      <div class="guide-actions">
        <el-button size="small" @click="loadStatus">重新检测</el-button>
        <el-button size="small" type="primary" @click="goAgentSettings">去下载助手</el-button>
      </div>
    </template>
  </el-alert>
</template>

<style scoped>
.amazon-integration-guide {
  margin-bottom: 16px;
}

.guide-steps {
  margin: 8px 0 8px 18px;
  padding: 0;
  line-height: 1.7;
}

.guide-note {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.guide-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.is-compact .guide-steps {
  font-size: 13px;
}
</style>
