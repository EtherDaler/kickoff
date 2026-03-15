<template>
  <div class="page">
    <header class="page-header">
      <button class="back-btn" @click="$router.back()">←</button>
      <h1>📊 Статистика</h1>
      <div style="width: 40px;"></div>
    </header>

    <div class="page-content">
      <div v-if="loading" class="loading-center"><div class="spinner"></div></div>

      <template v-else>
        <!-- Score -->
        <div class="card">
          <div class="card-body">
            <h3 class="form-section-title">Счёт матча</h3>
            <div class="score-input-row">
              <div class="score-input-group">
                <label class="form-label">Команда 1</label>
                <input v-model.number="form.team1_score" type="number" class="form-input score-input" min="0" />
              </div>
              <span class="score-sep">:</span>
              <div class="score-input-group">
                <label class="form-label">Команда 2</label>
                <input v-model.number="form.team2_score" type="number" class="form-input score-input" min="0" />
              </div>
            </div>
          </div>
        </div>

        <!-- Player stats -->
        <div style="margin-top: 12px;">
          <h3 class="section-title">Статистика игроков</h3>
          <div v-for="(ps, idx) in form.player_stats" :key="ps.user_id" class="player-stat-card card">
            <div class="card-body">
              <div class="player-stat-header">
                <div class="player-stat-name">
                  <span class="player-avatar-placeholder">{{ getPlayer(ps.user_id)?.first_name[0] }}</span>
                  <span>{{ getPlayer(ps.user_id)?.first_name }} {{ getPlayer(ps.user_id)?.last_name || '' }}</span>
                  <span v-if="ps.is_referee" class="badge badge-yellow">Судья</span>
                </div>
              </div>

              <template v-if="!ps.is_referee">
                <div class="stat-inputs-grid">
                  <div class="stat-input-item">
                    <label class="stat-input-label">⚽ Голы</label>
                    <input v-model.number="ps.goals" type="number" class="form-input stat-num" min="0" />
                  </div>
                  <div class="stat-input-item">
                    <label class="stat-input-label">🎯 Передачи</label>
                    <input v-model.number="ps.assists" type="number" class="form-input stat-num" min="0" />
                  </div>
                  <div class="stat-input-item">
                    <label class="stat-input-label">🟡 Ж.карт.</label>
                    <input v-model.number="ps.yellow_cards" type="number" class="form-input stat-num" min="0" max="2" />
                  </div>
                  <div class="stat-input-item">
                    <label class="stat-input-label">🔴 К.карт.</label>
                    <input v-model.number="ps.red_cards" type="number" class="form-input stat-num" min="0" max="1" />
                  </div>
                  <div class="stat-input-item">
                    <label class="stat-input-label">⚠️ Фолы</label>
                    <input v-model.number="ps.fouls" type="number" class="form-input stat-num" min="0" />
                  </div>
                </div>
                <div class="toggle-row" style="margin-top: 10px;">
                  <span class="toggle-label" style="font-size:14px;">🏥 Травма</span>
                  <label class="switch">
                    <input v-model="ps.is_injured" type="checkbox" />
                    <span class="slider"></span>
                  </label>
                </div>
                <div class="form-group" style="margin-top: 10px; margin-bottom: 0;">
                  <input v-model="ps.notes" class="form-input" placeholder="Заметки..." />
                </div>
              </template>
            </div>
          </div>
        </div>

        <div v-if="error" class="alert alert-error" style="margin-top: 12px;">{{ error }}</div>
        <div v-if="saved" class="alert alert-success" style="margin-top: 12px;">✅ Статистика сохранена!</div>

        <button
          class="btn btn-primary btn-full"
          style="margin-top: 16px;"
          :disabled="submitting"
          @click="submit"
        >
          {{ submitting ? 'Сохранение...' : '💾 Сохранить статистику' }}
        </button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { matchesApi } from '@/api'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const submitting = ref(false)
const error = ref('')
const saved = ref(false)
const match = ref(null)

const form = ref({
  team1_score: 0,
  team2_score: 0,
  player_stats: [],
})

function getPlayer(userId) {
  const p = match.value?.participants?.find(p => p.user.id === userId)
  return p?.user || null
}

onMounted(async () => {
  try {
    const res = await matchesApi.get(route.params.id)
    match.value = res.data
    const confirmed = res.data.participants.filter(p =>
      ['confirmed', 'pending_payment'].includes(p.status)
    )
    form.value.player_stats = confirmed.map(p => ({
      user_id: p.user.id,
      goals: 0,
      assists: 0,
      yellow_cards: 0,
      red_cards: 0,
      fouls: 0,
      is_injured: false,
      is_referee: p.role === 'referee',
      notes: '',
    }))

    try {
      const sr = await matchesApi.getStats(route.params.id)
      form.value.team1_score = sr.data.team1_score
      form.value.team2_score = sr.data.team2_score
      for (const existing of sr.data.player_stats) {
        const idx = form.value.player_stats.findIndex(ps => ps.user_id === existing.user.id)
        if (idx >= 0) {
          form.value.player_stats[idx] = {
            user_id: existing.user.id,
            goals: existing.goals,
            assists: existing.assists,
            yellow_cards: existing.yellow_cards,
            red_cards: existing.red_cards,
            fouls: existing.fouls,
            is_injured: existing.is_injured,
            is_referee: existing.is_referee,
            notes: existing.notes || '',
          }
        }
      }
    } catch { }
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})

async function submit() {
  submitting.value = true
  error.value = ''
  try {
    await matchesApi.submitStats(route.params.id, {
      team1_score: form.value.team1_score,
      team2_score: form.value.team2_score,
      player_stats: form.value.player_stats,
    })
    saved.value = true
    setTimeout(() => router.push(`/matches/${route.params.id}`), 1500)
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.page-header { justify-content: space-between; }
.back-btn {
  width: 40px; height: 40px;
  display: flex; align-items: center; justify-content: center;
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: var(--radius); cursor: pointer; font-size: 18px;
  color: var(--text-primary);
}

.form-section-title { font-size: 15px; font-weight: 700; margin-bottom: 14px; color: var(--text-secondary); }
.score-input-row { display: flex; align-items: flex-end; gap: 12px; justify-content: center; }
.score-input-group { display: flex; flex-direction: column; align-items: center; gap: 6px; flex: 1; max-width: 120px; }
.score-input { text-align: center; font-size: 28px; font-weight: 800; padding: 12px; }
.score-sep { font-size: 28px; font-weight: 700; color: var(--text-muted); padding-bottom: 12px; }

.section-title { font-size: 16px; font-weight: 700; margin-bottom: 10px; }
.player-stat-card { margin-bottom: 10px; }
.player-stat-header { margin-bottom: 12px; }
.player-stat-name { display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 15px; }
.player-avatar-placeholder {
  width: 32px; height: 32px;
  background: var(--bg-secondary); border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 14px; color: var(--text-secondary);
  flex-shrink: 0;
}
.stat-inputs-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.stat-input-item { display: flex; flex-direction: column; gap: 4px; }
.stat-input-label { font-size: 12px; color: var(--text-muted); font-weight: 500; }
.stat-num { padding: 8px; text-align: center; font-size: 16px; font-weight: 700; }

.toggle-row { display: flex; align-items: center; justify-content: space-between; }
.toggle-label { font-size: 15px; font-weight: 600; }
.switch { position: relative; width: 44px; height: 24px; flex-shrink: 0; }
.switch input { display: none; }
.slider {
  position: absolute; inset: 0;
  background: var(--bg-secondary); border: 1.5px solid var(--border);
  border-radius: 12px; cursor: pointer; transition: 0.25s;
}
.slider::before {
  content: ''; position: absolute;
  width: 18px; height: 18px; left: 2px; top: 1px;
  background: var(--text-muted); border-radius: 50%; transition: 0.25s;
}
.switch input:checked + .slider { background: var(--accent-glow); border-color: var(--accent); }
.switch input:checked + .slider::before { background: var(--accent); transform: translateX(20px); }
</style>
