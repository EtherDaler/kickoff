<template>
  <router-link :to="`/matches/${match.id}`" class="match-card">
    <div class="match-card__header">
      <div class="match-card__title-row">
        <h3 class="match-card__title">{{ match.title }}</h3>
        <span :class="['badge', statusBadge.class]">{{ statusBadge.label }}</span>
      </div>
      <div class="match-card__meta">
        <span class="meta-item">📍 {{ match.address }}</span>
        <span class="meta-item">📅 {{ formatDate(match.match_date) }}</span>
      </div>
    </div>
    <div class="match-card__footer">
      <div class="match-card__stats">
        <div class="match-stat">
          <span class="match-stat__icon">👥</span>
          <span class="match-stat__val">{{ match.confirmed_count }}/{{ match.max_players }}</span>
        </div>
        <div v-if="match.is_paid" class="match-stat">
          <span class="match-stat__icon">💰</span>
          <span class="match-stat__val">{{ match.price_per_player }} ₽</span>
        </div>
        <div v-else class="match-stat">
          <span class="match-stat__icon">🆓</span>
          <span class="match-stat__val">Бесплатно</span>
        </div>
      </div>
      <div class="match-card__vis">
        <span v-if="match.visibility === 'public'" class="badge badge-blue">🌍</span>
        <span v-else class="badge badge-gray">🔒</span>
      </div>
    </div>
    <div class="match-card__progress">
      <div
        class="match-card__progress-fill"
        :style="{ width: progressWidth }"
      ></div>
    </div>
  </router-link>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  match: { type: Object, required: true },
})

const statusMap = {
  upcoming: { label: 'Предстоящий', class: 'badge-blue' },
  ongoing: { label: 'В игре', class: 'badge-green' },
  finished: { label: 'Завершён', class: 'badge-gray' },
  cancelled: { label: 'Отменён', class: 'badge-red' },
}

const statusBadge = computed(() => statusMap[props.match.status] || { label: props.match.status, class: 'badge-gray' })

const progressWidth = computed(() => {
  const pct = (props.match.confirmed_count / props.match.max_players) * 100
  return `${Math.min(100, pct)}%`
})

function formatDate(dt) {
  const d = new Date(dt)
  return d.toLocaleString('ru-RU', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.match-card {
  display: block;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  text-decoration: none;
  color: inherit;
  transition: all 0.2s;
  position: relative;
}
.match-card:active { transform: scale(0.98); }
.match-card__header { padding: 14px 14px 10px; }
.match-card__title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}
.match-card__title {
  font-size: 15px;
  font-weight: 700;
  line-height: 1.3;
  flex: 1;
}
.match-card__meta {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.meta-item {
  font-size: 13px;
  color: var(--text-secondary);
}
.match-card__footer {
  padding: 10px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid var(--border);
}
.match-card__stats { display: flex; gap: 14px; }
.match-stat { display: flex; align-items: center; gap: 4px; }
.match-stat__icon { font-size: 14px; }
.match-stat__val { font-size: 13px; font-weight: 600; color: var(--text-secondary); }
.match-card__progress {
  height: 3px;
  background: var(--border);
}
.match-card__progress-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.4s ease;
}
</style>
