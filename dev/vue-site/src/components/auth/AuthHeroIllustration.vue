<script setup>
import { useYotoMascot } from '@/composables/useYotoMascot'

defineProps({
  hero: { type: Boolean, default: false },
})

const { coveringEyes } = useYotoMascot()
</script>

<template>
  <div class="hero-illus" :class="{ 'is-private': coveringEyes }" aria-hidden="true">
    <svg viewBox="0 0 400 320" class="hero-illus__svg">
      <defs>
        <linearGradient id="illusBg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#e8f3ff" />
          <stop offset="100%" stop-color="#f7f8fa" />
        </linearGradient>
        <linearGradient id="illusPrimary" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#165dff" />
          <stop offset="100%" stop-color="#4080ff" />
        </linearGradient>
        <filter id="illusShadow" x="-10%" y="-10%" width="120%" height="120%">
          <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#165dff" flood-opacity="0.12" />
        </filter>
      </defs>

      <rect width="400" height="320" rx="16" fill="url(#illusBg)" />

      <!-- floating card: chart -->
      <g filter="url(#illusShadow)" class="hero-illus__card hero-illus__card--1">
        <rect x="32" y="48" width="168" height="120" rx="10" fill="#fff" />
        <rect x="48" y="64" width="60" height="8" rx="4" fill="#e5e6eb" />
        <rect x="48" y="80" width="40" height="6" rx="3" fill="#f2f3f5" />
        <polyline
          points="48,140 72,118 96,128 120,100 144,108 168,88"
          fill="none"
          stroke="url(#illusPrimary)"
          stroke-width="3"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <circle cx="168" cy="88" r="4" fill="#165dff" />
      </g>

      <!-- floating card: stats -->
      <g filter="url(#illusShadow)" class="hero-illus__card hero-illus__card--2">
        <rect x="200" y="72" width="168" height="96" rx="10" fill="#fff" />
        <rect x="216" y="88" width="48" height="32" rx="6" fill="#e8f3ff" />
        <rect x="224" y="96" width="32" height="6" rx="3" fill="#165dff" opacity="0.6" />
        <rect x="224" y="108" width="20" height="4" rx="2" fill="#bedaff" />
        <rect x="276" y="88" width="48" height="32" rx="6" fill="#e8fffb" />
        <rect x="284" y="96" width="32" height="6" rx="3" fill="#14c9c9" opacity="0.6" />
        <rect x="328" y="88" width="24" height="32" rx="6" fill="#fff7e8" />
        <rect x="334" y="96" width="12" height="6" rx="3" fill="#ff7d00" opacity="0.5" />
        <rect x="216" y="136" width="120" height="6" rx="3" fill="#f2f3f5" />
      </g>

      <!-- floating card: table -->
      <g filter="url(#illusShadow)" class="hero-illus__card hero-illus__card--3">
        <rect x="72" y="188" width="256" height="100" rx="10" fill="#fff" />
        <rect x="88" y="204" width="80" height="6" rx="3" fill="#e5e6eb" />
        <rect x="88" y="224" width="224" height="1" fill="#f2f3f5" />
        <rect x="88" y="236" width="140" height="5" rx="2.5" fill="#f2f3f5" />
        <rect x="88" y="252" width="100" height="5" rx="2.5" fill="#f2f3f5" />
        <rect x="88" y="268" width="160" height="5" rx="2.5" fill="#f2f3f5" />
        <circle cx="296" cy="240" r="10" fill="#e8f3ff" />
        <path d="M292 240 L295 243 L300 236" fill="none" stroke="#165dff" stroke-width="2" stroke-linecap="round" />
      </g>

      <!-- accent dots -->
      <circle cx="360" cy="56" r="6" fill="#165dff" opacity="0.2" class="hero-illus__dot" />
      <circle cx="40" cy="200" r="4" fill="#14c9c9" opacity="0.25" class="hero-illus__dot hero-illus__dot--2" />
    </svg>

    <p v-if="coveringEyes && hero" class="hero-illus__hint">数据已加密 · 请放心输入</p>
  </div>
</template>

<style scoped>
.hero-illus {
  width: 100%;
  max-width: min(25rem, 100%);
  margin: 0 auto;
  transition: filter 0.3s ease;
}

.hero-illus.is-private .hero-illus__svg {
  filter: blur(2px) brightness(0.95);
}

.hero-illus__svg {
  width: 100%;
  height: auto;
  border-radius: 16px;
  overflow: hidden;
}

.hero-illus__card--1 {
  animation: float-card 5s ease-in-out infinite;
}

.hero-illus__card--2 {
  animation: float-card 5.5s ease-in-out infinite reverse;
}

.hero-illus__card--3 {
  animation: float-card 6s ease-in-out infinite;
  animation-delay: -1s;
}

.hero-illus__dot {
  animation: pulse-dot 3s ease-in-out infinite;
}

.hero-illus__dot--2 {
  animation-delay: 1.5s;
}

.hero-illus__hint {
  margin: 12px 0 0;
  text-align: center;
  font-size: 12px;
  color: var(--ch-text-muted);
}

@keyframes float-card {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

@keyframes pulse-dot {
  0%, 100% { opacity: 0.2; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(1.15); }
}

@media (prefers-reduced-motion: reduce) {
  .hero-illus__card--1,
  .hero-illus__card--2,
  .hero-illus__card--3,
  .hero-illus__dot {
    animation: none;
  }
}
</style>
