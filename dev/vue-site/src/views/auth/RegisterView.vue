<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowRight, Lock, OfficeBuilding, User } from '@element-plus/icons-vue'
import { registerCompany } from '@/api/auth'
import AuthSplitLayout from '@/components/auth/AuthSplitLayout.vue'
import { useYotoMascot } from '@/composables/useYotoMascot'

const router = useRouter()
const { onPasswordFocus, onPasswordBlur } = useYotoMascot()

const loading = ref(false)
const form = ref({
  company: '',
  account: '',
  password: '',
  confirmPassword: '',
})

async function handleRegister() {
  if (!form.value.company.trim()) {
    ElMessage.warning('请填写企业名称')
    return
  }
  if (!form.value.account.trim()) {
    ElMessage.warning('请填写登录账号')
    return
  }
  if (form.value.password.length < 6) {
    ElMessage.warning('密码至少 6 位')
    return
  }
  if (form.value.password !== form.value.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }

  loading.value = true
  try {
    await registerCompany({
      company: form.value.company.trim(),
      account: form.value.account.trim(),
      password: form.value.password,
    })
    ElMessage.success('注册成功，请登录')
    router.push({ path: '/login', query: { account: form.value.account.trim() } })
  } catch (err) {
    ElMessage.error(err.message || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthSplitLayout>
    <header class="auth-head">
      <p class="auth-head__eyebrow">Get started</p>
      <h2>注册 CrossHub</h2>
      <p class="auth-head__sub">创建企业账号，以企业管理员身份管理跨境业务</p>
    </header>

    <el-form label-position="top" class="auth-form" @submit.prevent="handleRegister">
      <el-form-item label="企业名称">
        <el-input
          v-model="form.company"
          :prefix-icon="OfficeBuilding"
          placeholder="如：杭州亿拓户外用品有限公司"
          size="large"
          clearable
        />
      </el-form-item>

      <el-form-item label="登录账号">
        <el-input
          v-model="form.account"
          :prefix-icon="User"
          placeholder="企业邮箱或登录账号"
          size="large"
          clearable
          autocomplete="username"
        />
      </el-form-item>

      <div class="password-row">
        <el-form-item label="登录密码">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :prefix-icon="Lock"
            placeholder="至少 6 位"
            size="large"
            autocomplete="new-password"
            @focus="onPasswordFocus"
            @blur="onPasswordBlur"
          />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            show-password
            :prefix-icon="Lock"
            placeholder="再次输入"
            size="large"
            autocomplete="new-password"
            @focus="onPasswordFocus"
            @blur="onPasswordBlur"
            @keyup.enter="handleRegister"
          />
        </el-form-item>
      </div>

      <el-button
        type="primary"
        size="large"
        class="auth-submit"
        :loading="loading"
        native-type="submit"
      >
        注册并创建企业
        <el-icon><ArrowRight /></el-icon>
      </el-button>
    </el-form>

    <p class="auth-switch-link">
      已有企业账号？
      <button type="button" class="auth-text-link" @click="router.push('/login')">返回登录</button>
    </p>
  </AuthSplitLayout>
</template>
