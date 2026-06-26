<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Bell, SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const menus = computed(() => auth.sidebarMenus)

const activeMenu = computed(() => route.path)
const pageTitle = computed(() => route.meta.title || 'CrossHub')

const userPanelTitle = computed(() =>
  auth.isBoss ? auth.company.name : auth.displayName,
)

const userPanelRole = computed(() =>
  auth.isBoss ? '企业管理员' : auth.employee.role || '运营专员',
)

const userPanelMeta = computed(() =>
  auth.isBoss ? auth.company.account : auth.employee.account,
)

const userInitial = computed(() => {
  const name = auth.isBoss ? auth.company.name : auth.employee.name
  return (name || 'U').slice(0, 1)
})

function handleLogout() {
  auth.logout()
  router.push('/login')
}

function handleUserCommand(command) {
  if (command === 'logout') handleLogout()
}
</script>

<template>
  <el-container class="portal">
    <el-aside width="220px" class="portal-aside">
      <div class="brand">
        <div class="brand-mark">CH</div>
        <div class="brand-text">
          <strong>CrossHub</strong>
          <span>{{ auth.portalLabel }}</span>
        </div>
      </div>

      <el-menu :default-active="activeMenu" router class="portal-menu">
        <el-menu-item v-for="item in menus" :key="item.index" :index="item.index">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>

      <div class="aside-footer">
        <el-dropdown
          trigger="click"
          placement="top-start"
          :show-arrow="false"
          popper-class="user-panel-popper"
          @command="handleUserCommand"
        >
          <div class="user-panel">
            <el-avatar :size="36" class="user-avatar">{{ userInitial }}</el-avatar>
            <div class="user-panel__body">
              <span class="user-panel__role">{{ userPanelRole }}</span>
              <p class="user-panel__name" :title="userPanelTitle">{{ userPanelTitle }}</p>
            </div>
            <el-icon class="user-panel__chevron"><SwitchButton /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled class="user-panel-menu__head">
                <div class="user-panel-menu__head-inner">
                  <p class="user-panel-menu__name">{{ userPanelTitle }}</p>
                  <p class="user-panel-menu__meta">{{ userPanelMeta }}</p>
                </div>
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-aside>

    <el-container class="portal-body">
      <el-header class="portal-header">
        <div class="header-title">
          <p class="header-eyebrow">{{ auth.portalLabel }}</p>
          <h2>{{ pageTitle }}</h2>
        </div>
        <div class="header-actions">
          <el-button :icon="Bell" circle class="icon-btn" />
        </div>
      </el-header>

      <el-main class="portal-main">
        <div class="portal-main-inner">
          <router-view v-slot="{ Component }">
            <component :is="Component" :key="route.path" class="portal-page" />
          </router-view>
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.portal {
  height: 100vh;
  overflow: hidden;
  background: var(--ch-layout-bg);
}

.portal-aside {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--ch-sidebar-bg);
  border-right: 1px solid var(--ch-sidebar-border);
  box-shadow: var(--ch-sidebar-shadow);
}

.portal > .el-container {
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.portal-body {
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.brand {
  display: flex;
  gap: 10px;
  align-items: center;
  height: 56px;
  padding: 0 16px;
  border-bottom: 1px solid var(--ch-border);
  flex-shrink: 0;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: var(--ch-radius-sm);
  background: var(--ch-primary);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
}

.brand-text strong {
  display: block;
  font-size: 15px;
  font-weight: 600;
  color: var(--ch-text);
  line-height: 1.3;
}

.brand-text span {
  display: block;
  font-size: 11px;
  color: var(--ch-text-muted);
}

.portal-menu {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 8px;
  border-right: none;
  background: transparent;
}

.portal-menu :deep(.el-menu-item) {
  position: relative;
  height: 42px;
  margin-bottom: 4px;
  border-radius: var(--ch-radius-sm);
  color: var(--ch-sidebar-text);
  font-size: 14px;
  font-weight: 400;
  line-height: 42px;
}

.portal-menu :deep(.el-menu-item:hover) {
  color: var(--ch-sidebar-text-hover);
  background: transparent;
}

.portal-menu :deep(.el-menu-item:hover::before) {
  content: '';
  position: absolute;
  inset: 0 4px;
  border-radius: var(--ch-radius-sm);
  background: var(--ch-surface-muted);
  z-index: -1;
}

.portal-menu :deep(.el-menu-item.is-active) {
  color: var(--ch-sidebar-text-active);
  font-weight: 500;
  background: transparent;
}

.portal-menu :deep(.el-menu-item.is-active::before) {
  content: '';
  position: absolute;
  inset: 0 4px;
  border-radius: var(--ch-radius-sm);
  background: var(--ch-sidebar-active-bg);
  z-index: -1;
}

.portal-menu :deep(.el-menu) {
  background: transparent;
  border: none;
}

.portal-menu :deep(.el-menu-item .el-icon) {
  font-size: 16px;
  color: inherit;
}

.aside-footer {
  padding: 10px;
  border-top: 1px solid var(--ch-border);
  flex-shrink: 0;
  background: var(--ch-surface);
}

.user-panel {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius-md);
  background: var(--ch-surface);
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}

.user-panel:hover {
  border-color: var(--ch-primary-muted);
  background: var(--ch-primary-soft);
  box-shadow: var(--ch-shadow-xs);
}

.user-panel__body {
  flex: 1;
  min-width: 0;
}

.user-avatar {
  flex-shrink: 0;
  background: linear-gradient(135deg, var(--ch-primary) 0%, #4080ff 100%);
  color: #fff;
  font-weight: 600;
  font-size: 14px;
}

.user-panel__role {
  display: inline-block;
  padding: 1px 6px;
  border-radius: var(--ch-radius-xs);
  font-size: 10px;
  font-weight: 500;
  line-height: 1.6;
  color: var(--ch-primary);
  background: var(--ch-primary-soft);
}

.user-panel__name {
  margin: 4px 0 0;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.45;
  color: var(--ch-text);
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  word-break: break-all;
}

.user-panel__chevron {
  flex-shrink: 0;
  font-size: 15px;
  color: var(--ch-text-muted);
  transition: color 0.15s ease;
}

.user-panel:hover .user-panel__chevron {
  color: var(--ch-primary);
}

.portal-header {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 24px;
  background: var(--ch-surface);
  border-bottom: 1px solid var(--ch-border);
  box-shadow: var(--ch-shadow-header);
}

.header-eyebrow {
  display: none;
}

.portal-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--ch-text);
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.icon-btn {
  font-size: 13px;
}

.portal-main {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding: 0 !important;
  background: var(--ch-layout-bg);
  display: flex;
  flex-direction: column;
}

.portal-main-inner {
  flex: 1;
  min-height: 0;
  padding: 16px 20px 20px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.portal-main-inner :deep(.portal-page) {
  flex: 1;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>

<style>
.user-panel-popper .user-panel-menu__head {
  height: auto !important;
  padding: 8px 16px 4px !important;
  cursor: default !important;
  opacity: 1 !important;
}

.user-panel-popper .user-panel-menu__head-inner {
  max-width: 200px;
}

.user-panel-popper .user-panel-menu__name {
  margin: 0;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.45;
  color: var(--ch-text);
  word-break: break-all;
}

.user-panel-popper .user-panel-menu__meta {
  margin: 4px 0 0;
  font-size: 12px;
  line-height: 1.4;
  color: var(--ch-text-muted);
  word-break: break-all;
}

.user-panel-popper .el-dropdown-menu__item:not(.is-disabled) {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
