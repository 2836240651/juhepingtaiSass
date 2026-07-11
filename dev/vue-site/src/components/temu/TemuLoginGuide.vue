<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchTemuSessionStatus, openTemuSellerLogin } from '@/api/temuApi'

const props = defineProps({
  compact: { type: Boolean, default: false },
})

const loading = ref(false)
const opening = ref(false)
const status = ref({})

const sessionReady = computed(() => Boolean(status.value.ready))
const mallNames = computed(() =>
  (status.value.malls || [])
    .map((mall) => mall.mall_name || mall.mallName)
    .filter(Boolean)
    .join('、'),
)

async function loadStatus() {
  loading.value = true
  try {
    status.value = await fetchTemuSessionStatus()
  } catch {
    status.value = { ready: false, requires_auth: true }
  } finally {
    loading.value = false
  }
}

async function handleOpenLogin() {
  if (status.value.profile_busy) {
    ElMessage.warning('登录窗口已在运行，请在已弹出的 CrossHub 浏览器中完成登录')
    return
  }
  opening.value = true
  try {
    const res = await openTemuSellerLogin()
    if (res.already_open) {
      ElMessage.warning(res.message || '登录窗口已在运行')
    } else {
      ElMessage.success(res.message || '已打开 Temu 登录窗口')
    }
    await loadStatus()
  } catch (err) {
    ElMessage.error(err.message || '打开登录窗口失败')
  } finally {
    opening.value = false
  }
}

onMounted(loadStatus)

defineExpose({ reload: loadStatus, sessionReady })
</script>

<template>
  <el-alert
    v-if="!loading && !sessionReady"
    type="warning"
    show-icon
    :closable="false"
    class="temu-login-guide"
    :class="{ 'is-compact': compact }"
    title="同步前需登录 Temu 卖家后台"
  >
    <template #default>
      <p class="guide-lead">
        请点击下方按钮，在 <strong>CrossHub 弹出的浏览器窗口</strong>（不是普通 Chrome）中登录 Temu 卖家后台。
        登录完成后点「我已完成登录」，再点「刷新数据」。
      </p>
      <ol class="guide-steps">
        <li>点击 <strong>打开登录窗口</strong>（若已弹出窗口可跳过）</li>
        <li>在 <strong>CrossHub 浏览器窗口</strong> 中用手机号登录 Temu 卖家后台</li>
        <li>登录后，在左上角 <strong>选择要同步的店铺</strong></li>
        <li>回到本页点击 <strong>我已完成登录</strong>，再点 <strong>刷新数据</strong></li>
      </ol>
      <p v-if="mallNames" class="guide-meta">已识别店铺：{{ mallNames }}</p>
      <div class="guide-actions">
        <el-button size="small" type="primary" :loading="opening" @click="handleOpenLogin">
          打开登录窗口
        </el-button>
        <el-button size="small" :loading="loading" @click="loadStatus">我已完成登录</el-button>
      </div>
    </template>
  </el-alert>
</template>

<style scoped>
.temu-login-guide {
  margin-bottom: 16px;
}

.guide-lead {
  margin: 0 0 8px;
  line-height: 1.6;
}

.guide-steps {
  margin: 8px 0 12px 18px;
  padding: 0;
  line-height: 1.7;
}

.guide-meta {
  margin: 0 0 10px;
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
