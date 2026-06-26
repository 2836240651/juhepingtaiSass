<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowRight, Lock, User, UserFilled } from '@element-plus/icons-vue'
import { loginBoss, loginEmployee } from '@/api/auth'
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
const password = ref('12345678')
const account = ref('admin@crosshub.cn')

const demoAccounts = [
  {
    role: 'boss',
    label: '企业管理员',
    account: 'admin@crosshub.cn',
    password: '12345678',
    hint: '全局总览',
  },
  {
    role: 'employee',
    label: '王一鸣',
    account: 'wangyiming@yituo-outdoor.com',
    password: 'Emp@Demo123',
    hint: 'Temu',
  },
  {
    role: 'employee',
    label: '赵磊',
    account: 'zhaolei@yituo-outdoor.com',
    password: 'Emp@Demo654',
    hint: '1688',
  },
  {
    role: 'employee',
    label: '刘洋',
    account: 'liuyang@yituo-outdoor.com',
    password: 'Emp@Demo987',
    hint: 'Amazon',
  },
  {
    role: 'employee',
    label: '周婷',
    account: 'zhouting@yituo-outdoor.com',
    password: 'Emp@Demo852',
    hint: 'Walmart',
  },
  {
    role: 'employee',
    label: '孙浩',
    account: 'sunhao@yituo-outdoor.com',
    password: 'Emp@Demo741',
    hint: '拼多多',
  },
  {
    role: 'employee',
    label: '林雪',
    account: 'linxue@yituo-outdoor.com',
    password: 'Emp@Demo963',
    hint: '抖音',
  },
  {
    role: 'employee',
    label: '何静',
    account: 'hejing@yituo-outdoor.com',
    password: 'Emp@Demo159',
    hint: '视频号',
  },
]

const roleLabel = computed(() => (portalRole.value === 'boss' ? '企业管理员' : '员工工作台'))

onMounted(() => {
  const q = route.query.account
  if (typeof q === 'string' && q) {
    account.value = q
    password.value = ''
    portalRole.value = 'employee'
  }
})

function fillDemo(demo) {
  portalRole.value = demo.role
  account.value = demo.account
  password.value = demo.password
}

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
        企业管理员
      </button>
      <button
        type="button"
        class="role-tab"
        :class="{ 'is-active': portalRole === 'employee' }"
        @click="portalRole = 'employee'"
      >
        <el-icon><User /></el-icon>
        员工端口
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
        @click="handleLogin"
      >
        进入{{ roleLabel }}
        <el-icon><ArrowRight /></el-icon>
      </el-button>
    </el-form>

    <p class="auth-switch-link">
      还没有企业账号？
      <button type="button" class="auth-text-link" @click="router.push('/register')">免费注册</button>
    </p>

    <section class="demo-section">
      <div class="demo-section__head">
        <span class="demo-section__label">Demo 账号</span>
        <span class="demo-section__hint">点击快速填充</span>
      </div>
      <div class="demo-grid">
        <button
          v-for="demo in demoAccounts"
          :key="demo.account"
          type="button"
          class="demo-chip"
          @click="fillDemo(demo)"
        >
          <strong>{{ demo.label }}</strong>
          <span>{{ demo.hint }}</span>
        </button>
      </div>
    </section>
  </AuthSplitLayout>
</template>
