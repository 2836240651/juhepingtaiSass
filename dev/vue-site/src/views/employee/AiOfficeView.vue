<script setup>
import { computed, ref } from 'vue'
import { ChatDotRound, Cpu, Lightning } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { AI_CONTEXT_HINTS, AI_SKILL_GROUPS } from '@/constants/aiOffice'
import { PLATFORM_OPTIONS } from '@/constants/employees'
import { platformDisplayLabels } from '@/constants/platforms'
import AiChatPanel from '@/components/ai/AiChatPanel.vue'

const auth = useAuthStore()
const chatRef = ref(null)
const activeGroup = ref(AI_SKILL_GROUPS[0].id)

const platformLabels = computed(() => {
  const map = Object.fromEntries(PLATFORM_OPTIONS.map((p) => [p.value, p.label]))
  const list = auth.backendLinked ? (auth.platforms || []) : (auth.employee.platforms || [])
  return platformDisplayLabels(list, map).join(' · ') || '运营'
})

const activeSkills = computed(
  () => AI_SKILL_GROUPS.find((g) => g.id === activeGroup.value)?.skills || [],
)

function runSkill(prompt) {
  chatRef.value?.sendMessage?.(prompt)
}
</script>

<template>
  <div class="ai-office">
    <header class="ai-hero">
      <div class="ai-hero__brand">
        <div class="ai-hero__icon">
          <el-icon><Cpu /></el-icon>
        </div>
        <div>
          <h1 class="ai-hero__title">CrossHub AI</h1>
          <p class="ai-hero__sub">
            {{ auth.employee.name }} · {{ auth.employee.role }}
            <span v-if="platformLabels" class="ai-hero__platform">{{ platformLabels }}</span>
          </p>
        </div>
      </div>
      <div class="ai-hero__meta">
        <span class="ai-hero__model">
          <el-icon><Lightning /></el-icon>
          Copilot
        </span>
      </div>
    </header>

    <div class="ai-body">
      <aside class="ai-skills">
        <p class="ai-skills__label">AI 技能</p>
        <div class="ai-skills__tabs">
          <button
            v-for="group in AI_SKILL_GROUPS"
            :key="group.id"
            type="button"
            class="skill-tab"
            :class="{ 'is-active': activeGroup === group.id }"
            :style="activeGroup === group.id ? { '--tab-color': group.color } : {}"
            @click="activeGroup = group.id"
          >
            {{ group.label }}
          </button>
        </div>
        <div class="skill-list">
          <button
            v-for="skill in activeSkills"
            :key="skill.id"
            type="button"
            class="skill-item"
            @click="runSkill(skill.prompt)"
          >
            <span class="skill-item__label">{{ skill.label }}</span>
            <span class="skill-item__desc">{{ skill.desc }}</span>
          </button>
        </div>
      </aside>

      <main class="ai-chat">
        <AiChatPanel
          ref="chatRef"
          scope="employee"
          :user-name="auth.employee.name"
          :platforms="platformLabels"
        />
      </main>

      <aside class="ai-context">
        <section class="context-block">
          <h3 class="context-block__title">
            <el-icon><ChatDotRound /></el-icon>
            工作上下文
          </h3>
          <div class="context-stats">
            <div v-for="item in AI_CONTEXT_HINTS" :key="item.label" class="context-stat">
              <span class="context-stat__value" :class="`is-${item.type}`">{{ item.value }}</span>
              <span class="context-stat__label">{{ item.label }}</span>
            </div>
          </div>
        </section>

        <section class="context-block">
          <h3 class="context-block__title">能力说明</h3>
          <ul class="context-list">
            <li>Listing 标题、卖点与多语言润色</li>
            <li>差评 / 买家消息 / Case 回复草稿</li>
            <li>补货、滞销、亏损 SKU 决策建议</li>
            <li>今日待办与预警优先级排序</li>
          </ul>
        </section>

        <section class="context-block context-block--muted">
          <p class="context-note">
            正式版将接入你负责店铺的真实订单、库存与任务数据，生成可执行的运营建议。
          </p>
        </section>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.ai-office {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
}

.ai-hero {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 20px;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding: 16px 20px;
  border-radius: var(--ch-radius-lg);
  border: 1px solid var(--ch-border);
  background: linear-gradient(135deg, var(--ch-primary-soft) 0%, var(--ch-surface) 55%);
}

.ai-hero__brand {
  display: flex;
  gap: 14px;
  align-items: center;
}

.ai-hero__icon {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: var(--ch-radius-md);
  background: linear-gradient(135deg, var(--ch-primary) 0%, #4080ff 100%);
  color: #fff;
  font-size: 22px;
  box-shadow: 0 4px 12px rgba(22, 93, 255, 0.3);
}

.ai-hero__title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--ch-text);
  line-height: 1.3;
}

.ai-hero__sub {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--ch-text-secondary);
}

.ai-hero__platform {
  margin-left: 6px;
  padding: 1px 8px;
  border-radius: var(--ch-radius-xs);
  background: var(--ch-surface);
  color: var(--ch-primary);
  font-size: 12px;
}

.ai-hero__meta {
  display: flex;
  gap: 10px;
  align-items: center;
}

.ai-hero__model {
  display: inline-flex;
  gap: 4px;
  align-items: center;
  padding: 4px 10px;
  border-radius: var(--ch-radius-sm);
  background: var(--ch-surface);
  border: 1px solid var(--ch-border);
  font-size: 12px;
  font-weight: 500;
  color: var(--ch-text-secondary);
}

.ai-body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 220px 1fr 240px;
  gap: 14px;
}

.ai-skills {
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 14px;
  border-radius: var(--ch-radius-lg);
  border: 1px solid var(--ch-border);
  background: var(--ch-surface);
}

.ai-skills__label {
  margin: 0 0 10px;
  font-size: 12px;
  font-weight: 600;
  color: var(--ch-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.ai-skills__tabs {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}

.skill-tab {
  padding: 8px 10px;
  border: none;
  border-radius: var(--ch-radius-sm);
  background: transparent;
  color: var(--ch-text-secondary);
  font-size: 13px;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.skill-tab:hover {
  background: var(--ch-surface-muted);
  color: var(--ch-text);
}

.skill-tab.is-active {
  background: var(--ch-primary-soft);
  color: var(--tab-color, var(--ch-primary));
  font-weight: 600;
}

.skill-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.skill-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius-sm);
  background: var(--ch-surface);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, box-shadow 0.15s;
}

.skill-item:hover {
  border-color: var(--ch-primary-muted);
  background: var(--ch-primary-soft);
  box-shadow: var(--ch-shadow-xs);
}

.skill-item__label {
  font-size: 13px;
  font-weight: 600;
  color: var(--ch-text);
}

.skill-item__desc {
  font-size: 11px;
  color: var(--ch-text-muted);
}

.ai-chat {
  min-height: 0;
  min-width: 0;
}

.ai-context {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  overflow-y: auto;
}

.context-block {
  padding: 14px;
  border-radius: var(--ch-radius-lg);
  border: 1px solid var(--ch-border);
  background: var(--ch-surface);
}

.context-block--muted {
  background: var(--ch-surface-muted);
  border-style: dashed;
}

.context-block__title {
  display: flex;
  gap: 6px;
  align-items: center;
  margin: 0 0 12px;
  font-size: 13px;
  font-weight: 600;
  color: var(--ch-text);
}

.context-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.context-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px;
  border-radius: var(--ch-radius-sm);
  background: var(--ch-surface-muted);
  text-align: center;
}

.context-stat__value {
  font-size: 18px;
  font-weight: 700;
  line-height: 1.2;
}

.context-stat__value.is-primary {
  color: var(--ch-primary);
}

.context-stat__value.is-warning {
  color: var(--ch-warning);
}

.context-stat__value.is-danger {
  color: var(--ch-error);
}

.context-stat__label {
  font-size: 10px;
  color: var(--ch-text-muted);
}

.context-list {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  line-height: 1.7;
  color: var(--ch-text-secondary);
}

.context-note {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--ch-text-muted);
}

@media (max-width: 1100px) {
  .ai-body {
    grid-template-columns: 200px 1fr;
  }

  .ai-context {
    display: none;
  }
}

@media (max-width: 768px) {
  .ai-body {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }

  .ai-skills {
    max-height: 200px;
  }

  .ai-skills__tabs {
    flex-direction: row;
    flex-wrap: wrap;
  }
}
</style>
