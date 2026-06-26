<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Lock, Plus, User } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import PageScroll from '@/components/common/PageScroll.vue'
import {
  deleteEmployee,
  fetchAssignableMenus,
  fetchEmployees,
  saveEmployee,
  toggleEmployeeStatus,
} from '@/api/employees'
import { fetchAllPlatformStores } from '@/api/platformAccounts'
import {
  PLATFORM_OPTION_GROUPS,
  ROLE_OPTIONS,
  platformLabels,
} from '@/constants/employees'

const loading = ref(false)
const employees = ref([])
const boundStores = ref([])
const assignableMenus = ref([])
const showForm = ref(false)

const storeNameMap = computed(() =>
  Object.fromEntries(boundStores.value.map((store) => [store.id, store.storeName])),
)

const availableStores = computed(() => {
  if (!form.platforms.length) return []
  const platformSet = new Set(form.platforms)
  return boundStores.value.filter((store) => platformSet.has(store.platform))
})

const emptyForm = () => ({
  id: '',
  name: '',
  account: '',
  password: '',
  phone: '',
  role: '',
  platforms: [],
  assignedStoreIds: [],
  menuCodes: [],
  status: true,
})

const form = reactive(emptyForm())

async function loadEmployees() {
  loading.value = true
  try {
    const [empRes, storeRes, menuRes] = await Promise.all([
      fetchEmployees(),
      fetchAllPlatformStores(),
      fetchAssignableMenus(),
    ])
    employees.value = empRes.data || []
    boundStores.value = storeRes.data || []
    assignableMenus.value = menuRes.data || []
  } catch {
    employees.value = []
    boundStores.value = []
    assignableMenus.value = []
  } finally {
    loading.value = false
  }
}

function openCreate() {
  Object.assign(form, emptyForm())
  showForm.value = true
}

function openEdit(row) {
  Object.assign(form, {
    id: row.id,
    name: row.name,
    account: row.account,
    password: '',
    phone: row.phone || '',
    role: row.role,
    platforms: [...(row.platforms || [])],
    assignedStoreIds: [...(row.assignedStoreIds || [])],
    menuCodes: [...(row.menuCodes || row.menu_codes || [])],
    status: row.status !== false,
  })
  showForm.value = true
}

function cancelForm() {
  showForm.value = false
  Object.assign(form, emptyForm())
}

async function submitForm() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写员工姓名')
    return
  }
  if (!form.account.trim()) {
    ElMessage.warning('请填写登录账号')
    return
  }
  if (!form.role) {
    ElMessage.warning('请选择岗位角色')
    return
  }
  if (!form.platforms.length) {
    ElMessage.warning('请至少选择一个负责平台')
    return
  }
  if (!form.id && !form.password) {
    ElMessage.warning('请设置初始登录密码')
    return
  }

  loading.value = true
  try {
    await saveEmployee({
      id: form.id || undefined,
      name: form.name.trim(),
      account: form.account.trim(),
      password: form.password,
      phone: form.phone.trim(),
      role: form.role,
      platforms: form.platforms,
      assignedStoreIds: form.assignedStoreIds,
      menuCodes: form.menuCodes,
      status: form.status,
    })
    ElMessage.success(form.id ? '员工信息已更新' : '员工绑定成功')
    cancelForm()
    await loadEmployees()
  } catch (err) {
    ElMessage.error(err.message || '保存失败')
  } finally {
    loading.value = false
  }
}

async function removeEmployee(row) {
  try {
    await ElMessageBox.confirm(`确定解除「${row.name}」的员工绑定？`, '确认', {
      type: 'warning',
      confirmButtonText: '解除',
      cancelButtonText: '取消',
    })
    await deleteEmployee(row.id)
    ElMessage.success('已解除绑定')
    await loadEmployees()
  } catch {
    // cancelled
  }
}

async function handleStatusChange(row, status) {
  try {
    await toggleEmployeeStatus(row.id, status)
    row.status = status
    ElMessage.success(status ? '已启用' : '已停用')
  } catch (err) {
    ElMessage.error(err.message || '操作失败')
    await loadEmployees()
  }
}

watch(
  () => form.platforms.slice(),
  () => {
    const allowed = new Set(availableStores.value.map((store) => store.id))
    form.assignedStoreIds = form.assignedStoreIds.filter((id) => allowed.has(id))
  },
)

onMounted(loadEmployees)
</script>

<template>
  <PageScroll>
    <template #header>
      <PageHeader
        title="员工信息绑定"
        description="绑定员工账号、负责平台与店铺，员工登录后仅可查看对应数据"
      >
        <template #actions>
          <el-button type="primary" :icon="Plus" @click="openCreate">添加员工</el-button>
        </template>
      </PageHeader>
    </template>

    <el-card v-if="showForm" shadow="never" class="form-card">
      <template #header>
        <span>{{ form.id ? '编辑员工' : '添加员工' }}</span>
      </template>

      <el-form label-width="100px" class="employee-form">
        <el-row :gutter="16">
          <el-col :xs="24" :md="12">
            <el-form-item label="员工姓名" required>
              <el-input v-model="form.name" :prefix-icon="User" placeholder="真实姓名" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="登录账号" required>
              <el-input v-model="form.account" placeholder="邮箱或手机号" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item :label="form.id ? '重置密码' : '登录密码'" :required="!form.id">
              <el-input
                v-model="form.password"
                type="password"
                show-password
                :prefix-icon="Lock"
                :placeholder="form.id ? '留空则不修改' : '员工端登录密码'"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="联系电话">
              <el-input v-model="form.phone" placeholder="选填" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="岗位角色" required>
              <el-select v-model="form.role" placeholder="选择岗位" style="width: 100%">
                <el-option
                  v-for="role in ROLE_OPTIONS"
                  :key="role"
                  :label="role"
                  :value="role"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="负责平台" required>
              <el-select
                v-model="form.platforms"
                multiple
                collapse-tags
                collapse-tags-tooltip
                placeholder="选择平台"
                style="width: 100%"
              >
                <el-option-group
                  v-for="group in PLATFORM_OPTION_GROUPS"
                  :key="group.label"
                  :label="group.label"
                >
                  <el-option
                    v-for="item in group.options"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-option-group>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24">
            <el-form-item label="负责店铺">
              <el-select
                v-model="form.assignedStoreIds"
                multiple
                collapse-tags
                collapse-tags-tooltip
                :disabled="!form.platforms.length"
                :placeholder="form.platforms.length ? '选择该员工负责的店铺' : '请先选择负责平台'"
                style="width: 100%"
              >
                <el-option
                  v-for="store in availableStores"
                  :key="store.id"
                  :label="store.storeName"
                  :value="store.id"
                >
                  <span>{{ store.storeName }}</span>
                  <el-text size="small" type="info" style="margin-left: 8px">
                    {{ platformLabels([store.platform]) }}
                  </el-text>
                </el-option>
              </el-select>
              <el-text size="small" type="info" tag="p" style="margin-top: 6px">
                同一店铺只能分配给一名员工，运营总览将按店铺展示问题与负责人
              </el-text>
            </el-form-item>
          </el-col>
          <el-col :xs="24">
            <el-form-item label="菜单权限">
              <el-select
                v-model="form.menuCodes"
                multiple
                collapse-tags
                collapse-tags-tooltip
                :disabled="!assignableMenus.length"
                :placeholder="assignableMenus.length ? '可选：精确指定员工可见菜单' : '连接后端后可分配菜单'"
                style="width: 100%"
              >
                <el-option
                  v-for="menu in assignableMenus"
                  :key="menu.code"
                  :label="menu.label"
                  :value="menu.code"
                />
              </el-select>
              <el-text size="small" type="info" tag="p" style="margin-top: 6px">
                不选则按「负责平台」自动推导；选定后仅显示勾选的运营模块（工作台等基础菜单始终可见）
              </el-text>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="账号状态">
              <el-switch v-model="form.status" active-text="启用" inactive-text="停用" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-space>
            <el-button type="primary" :loading="loading" @click="submitForm">
              {{ form.id ? '保存修改' : '确认绑定' }}
            </el-button>
            <el-button @click="cancelForm">取消</el-button>
          </el-space>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <el-space>
          <span>已绑定员工</span>
          <el-tag type="info" size="small">{{ employees.length }} 人</el-tag>
        </el-space>
      </template>

      <el-table v-loading="loading" :data="employees" stripe>
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="role" label="岗位" width="130" />
        <el-table-column label="负责平台" min-width="140">
          <template #default="{ row }">
            <el-space wrap :size="4">
              <el-tag
                v-for="p in row.platforms"
                :key="p"
                size="small"
                effect="plain"
              >
                {{ platformLabels([p]) }}
              </el-tag>
            </el-space>
          </template>
        </el-table-column>
        <el-table-column label="负责店铺" min-width="180">
          <template #default="{ row }">
            <el-space v-if="row.assignedStoreIds?.length" wrap :size="4">
              <el-tag
                v-for="storeId in row.assignedStoreIds"
                :key="storeId"
                size="small"
                type="primary"
                effect="plain"
              >
                {{ storeNameMap[storeId] || storeId }}
              </el-tag>
            </el-space>
            <el-text v-else size="small" type="info">未分配店铺</el-text>
          </template>
        </el-table-column>
        <el-table-column label="菜单权限" min-width="160">
          <template #default="{ row }">
            <el-space v-if="row.menuCodes?.length" wrap :size="4">
              <el-tag
                v-for="code in row.menuCodes"
                :key="code"
                size="small"
                type="warning"
                effect="plain"
              >
                {{ assignableMenus.find((m) => m.code === code)?.label || code }}
              </el-tag>
            </el-space>
            <el-text v-else size="small" type="info">按平台推导</el-text>
          </template>
        </el-table-column>
        <el-table-column prop="account" label="登录账号" min-width="180" show-overflow-tooltip />
        <el-table-column prop="phone" label="联系电话" width="130">
          <template #default="{ row }">
            {{ row.phone || '—' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.status !== false"
              size="small"
              @change="(val) => handleStatusChange(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="boundAt" label="绑定时间" width="170" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" :icon="Delete" @click="removeEmployee(row)">
              解除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </PageScroll>
</template>

<style scoped>
.form-card {
  margin-bottom: 16px;
}

.employee-form {
  max-width: 800px;
}
</style>
