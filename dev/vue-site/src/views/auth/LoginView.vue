<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowRight, Box, Lock, User, UserFilled } from '@element-plus/icons-vue'
import { loginBoss, loginEmployee, loginWarehouse } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { defaultLandingPath } from '@/utils/menuAuth'
import AuthSplitLayout from '@/components/auth/AuthSplitLayout.vue'
import { useYotoMascot } from '@/composables/useYotoMascot'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { onPasswordFocus, onPasswordBlur } = useYotoMascot()

const loading = ref(false)
const portalRole = ref('boss')
const password = ref('')
const account = ref('')

const roleLabel = computed(() => {
  if (portalRole.value === 'boss') return '企业管理员'
  if (portalRole.value === 'warehouse') return '仓库端口'
  return '员工工作台'
})

onMounted(() => {
  const q = route.query.account
  if (typeof q === 'string' && q) {
    account.value = q
    password.value = ''
    portalRole.value = 'employee'
  }
})

async function handleLogin() {
  if (!account.value.trim()) {
    ElMessage.warning('请填写账号')
    return
  }
  if (!password.value) {
    ElMessage.warning('请填写密码')
    return
  }

  loading.value = true
  try {
    if (portalRole.value === 'boss') {
      const res = await loginBoss({
        account: account.value.trim(),
        password: password.value,
      })
      auth.setCompany(res.data)
      auth.login('boss')
      router.push(defaultLandingPath(auth))
    } else if (portalRole.value === 'warehouse') {
      const res = await loginWarehouse({
        account: account.value.trim(),
        password: password.value,
      })
      auth.setWarehouse(res.data)
      auth.login('warehouse')
      router.push(defaultLandingPath(auth))
    } else {
      const res = await loginEmployee({
        account: account.value.trim(),
        password: password.value,
      })
      auth.setEmployee(res.data)
      auth.login('employee')
      router.push(defaultLandingPath(auth))
    }
  } catch (err) {
    ElMessage.error(err.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthSplitLayout>
    <header class="auth-head">
      <p class="auth-head__eyebrow">Welcome back</p>
      <h2>登录 CrossHub</h2>
      <p class="auth-head__sub">选择身份，进入对应工作台</p>
    </header>

    <div class="role-tabs">
      <button
        type="button"
        class="role-tab"
        :class="{ 'is-active': portalRole === 'boss' }"
        @click="portalRole = 'boss'"
      >
        <el-icon><UserFilled /></el-icon>
        <span class="role-tab__text">企业管理员</span>
      </button>
      <button
        type="button"
        class="role-tab"
        :class="{ 'is-active': portalRole === 'employee' }"
        @click="portalRole = 'employee'"
      >
        <el-icon><User /></el-icon>
        <span class="role-tab__text">员工端口</span>
      </button>
      <button
        type="button"
        class="role-tab"
        :class="{ 'is-active': portalRole === 'warehouse' }"
        @click="portalRole = 'warehouse'"
      >
        <el-icon><Box /></el-icon>
        <span class="role-tab__text">仓库端口</span>
      </button>
    </div>

    <el-form label-position="top" class="auth-form" @submit.prevent="handleLogin">
      <el-form-item label="账号">
        <el-input
          v-model="account"
          :prefix-icon="User"
          placeholder="企业邮箱或登录账号"
          size="large"
          clearable
          autocomplete="username"
        />
      </el-form-item>
      <el-form-item label="密码">
        <el-input
          v-model="password"
          type="password"
          show-password
          :prefix-icon="Lock"
          placeholder="请输入密码"
          size="large"
          autocomplete="current-password"
          @focus="onPasswordFocus"
          @blur="onPasswordBlur"
          @keyup.enter="handleLogin"
        />
      </el-form-item>

      <el-button
        type="primary"
        size="large"
        class="auth-submit"
        :loading="loading"
        native-type="submit"
      >
        进入{{ roleLabel }}
        <el-icon><ArrowRight /></el-icon>
      </el-button>
    </el-form>

    <p class="auth-switch-link">
      还没有企业账号？
      <button type="button" class="auth-text-link" @click="router.push('/register')">免费注册</button>
    </p>
  </AuthSplitLayout>
</template>
