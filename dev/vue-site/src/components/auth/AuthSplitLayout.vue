<script setup>
import AuthHeroIllustration from './AuthHeroIllustration.vue'
</script>

<template>
  <div class="auth-split">
    <aside class="auth-split__hero">
      <div class="hero-stack">
        <header class="hero-top">
          <div class="hero-brand">
            <div class="hero-brand__mark">CH</div>
            <span class="hero-brand__name">CrossHub</span>
          </div>
        </header>

        <div class="hero-copy">
          <h1 class="hero-copy__title">跨境运营指挥台</h1>
          <p class="hero-copy__desc">多平台数据整合 · 智能预警 · 分级权限管理</p>
          <ul class="hero-copy__features">
            <li>Temu / Amazon / 1688 全平台覆盖</li>
            <li>企业管理员与员工分级工作台</li>
            <li>运营问题实时追踪与协同</li>
          </ul>
        </div>

        <div class="hero-stage">
          <AuthHeroIllustration hero />
        </div>
      </div>
    </aside>

    <main class="auth-split__main">
      <div class="auth-panel">
        <slot />
      </div>
    </main>
  </div>
</template>

<style scoped>
.auth-split {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  width: 100%;
  min-height: 100dvh;
  overflow-x: clip;
  overflow-y: auto;
}

.auth-split__hero,
.auth-split__main {
  flex: 1 1 0;
  min-width: 0;
  box-sizing: border-box;
}

.auth-split__hero {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: clamp(1.25rem, 3vw, 3rem);
  background: var(--ch-surface);
  border-right: 1px solid var(--ch-border);
}

.hero-stack {
  display: flex;
  flex-direction: column;
  gap: clamp(1.25rem, 2.5vw, 2.5rem);
  width: 100%;
  max-width: 26.25rem;
  margin: 0 auto;
}

.hero-top {
  display: flex;
  flex-shrink: 0;
  align-items: center;
}

.hero-brand {
  display: flex;
  align-items: center;
  gap: 0.625rem;
}

.hero-brand__mark {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: var(--ch-radius-sm);
  background: var(--ch-primary);
  font-size: 0.75rem;
  font-weight: 700;
  color: #fff;
}

.hero-brand__name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--ch-text);
}

.hero-copy {
  flex-shrink: 0;
}

.hero-copy__title {
  margin: 0;
  font-size: clamp(1.5rem, 2.2vw, 2rem);
  font-weight: 600;
  line-height: 1.25;
  letter-spacing: -0.02em;
  color: var(--ch-text);
}

.hero-copy__desc {
  margin: 0.75rem 0 0;
  font-size: clamp(0.875rem, 1.1vw, 0.9375rem);
  line-height: 1.6;
  color: var(--ch-text-secondary);
}

.hero-copy__features {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  margin: 1.25rem 0 0;
  padding: 0;
  list-style: none;
}

.hero-copy__features li {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  font-size: clamp(0.8125rem, 1vw, 0.875rem);
  line-height: 1.5;
  color: var(--ch-text-secondary);
}

.hero-copy__features li::before {
  content: '';
  flex-shrink: 0;
  width: 0.375rem;
  height: 0.375rem;
  margin-top: 0.45em;
  border-radius: 50%;
  background: var(--ch-primary);
}

.hero-stage {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.auth-split__main {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: clamp(1.25rem, 3vw, 3rem);
  background: var(--ch-layout-bg);
}

.auth-panel {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 25rem;
  margin: 0 auto;
  padding: clamp(1.5rem, 2.5vw, 2.25rem) clamp(1.25rem, 2vw, 2rem);
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius-lg);
  background: var(--ch-surface);
  box-shadow: var(--ch-shadow-sm);
  box-sizing: border-box;
}

@media (max-width: 1080px) {
  .auth-split {
    flex-direction: column;
    min-height: 100dvh;
  }

  .auth-split__main {
    order: -1;
    align-items: flex-start;
    width: 100%;
    padding: max(1rem, env(safe-area-inset-top)) 1rem 1.5rem;
  }

  .auth-panel {
    max-width: 30rem;
    border: none;
    box-shadow: none;
    padding: 1.5rem 0.25rem 0.5rem;
  }

  .auth-split__hero {
    width: 100%;
    border-right: none;
    border-top: 1px solid var(--ch-border);
    padding: 1.25rem 1rem max(1.5rem, env(safe-area-inset-bottom));
  }

  .hero-stack {
    max-width: 30rem;
    gap: 1rem;
  }

  .hero-stage {
    display: none;
  }
}

@media (max-width: 480px) {
  .auth-split__main {
    padding-left: 0.75rem;
    padding-right: 0.75rem;
  }

  .auth-panel {
    padding: 1.25rem 0 0.25rem;
  }

  .hero-copy__features {
    display: none;
  }
}
</style>
