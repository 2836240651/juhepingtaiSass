<template>
  <div class="auth-shell">
    <router-view />
  </div>
</template>

<style scoped>
.auth-shell {
  display: flex;
  flex-direction: column;
  width: 100%;
  min-height: 100dvh;
  overflow-x: clip;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  background: var(--ch-layout-bg);
}

.auth-shell > * {
  flex: 1 0 auto;
  width: 100%;
  min-height: 100dvh;
}
</style>
