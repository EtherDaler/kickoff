<template>
  <div class="page">
    <header class="page-header">
      <button class="back-btn" @click="$router.back()">←</button>
      <h1>Редактировать матч</h1>
      <div style="width: 40px;"></div>
    </header>

    <div class="page-content">
      <div v-if="loading" class="loading-center"><div class="spinner"></div></div>
      <div v-else-if="loadError" class="alert alert-error">{{ loadError }}</div>

      <template v-else>
        <div v-if="success" class="alert alert-success">
          ✅ Матч обновлён! Участники получили уведомление.
        </div>

        <form @submit.prevent="submit">
          <!-- Basic Info -->
          <div class="card">
            <div class="card-body">
              <h3 class="form-section-title">Основная информация</h3>
              <div class="form-group">
                <label class="form-label">Название *</label>
                <input v-model="form.title" class="form-input" placeholder="Воскресный матч" required />
              </div>
              <div class="form-group">
                <label class="form-label">Адрес *</label>
                <input v-model="form.address" class="form-input" placeholder="ул. Ленина, 10" required />
              </div>
              <div class="form-row">
                <div class="form-group form-group--half">
                  <label class="form-label">Дата и время *</label>
                  <input v-model="form.match_date" type="datetime-local" class="form-input" required />
                </div>
                <div class="form-group form-group--half">
                  <label class="form-label">Игроков *</label>
                  <input v-model.number="form.max_players" type="number" class="form-input" min="2" max="50" required />
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">Описание</label>
                <textarea
                  v-model="form.description"
                  class="form-input"
                  placeholder="Дополнительная информация..."
                  rows="3"
                ></textarea>
              </div>
            </div>
          </div>

          <!-- Settings -->
          <div class="card" style="margin-top: 12px;">
            <div class="card-body">
              <h3 class="form-section-title">Настройки</h3>

              <div class="toggle-row">
                <div>
                  <span class="toggle-label">Видимость</span>
                  <p class="toggle-desc">Публичный матч виден всем</p>
                </div>
                <div class="seg-control">
                  <button
                    type="button"
                    :class="['seg-btn', { active: form.visibility === 'public' }]"
                    @click="form.visibility = 'public'"
                  >🌍 Публичный</button>
                  <button
                    type="button"
                    :class="['seg-btn', { active: form.visibility === 'private' }]"
                    @click="form.visibility = 'private'"
                  >🔒 Закрытый</button>
                </div>
              </div>

              <div class="divider"></div>

              <div class="toggle-row">
                <div>
                  <span class="toggle-label">💰 Платный</span>
                  <p class="toggle-desc">Участники должны оплатить</p>
                </div>
                <label class="switch">
                  <input v-model="form.is_paid" type="checkbox" />
                  <span class="slider"></span>
                </label>
              </div>

              <transition name="slide-up">
                <div v-if="form.is_paid" class="form-group" style="margin-top: 12px;">
                  <label class="form-label">Стоимость (₽ / чел.)</label>
                  <input
                    v-model.number="form.price_per_player"
                    type="number"
                    class="form-input"
                    min="0"
                    step="50"
                  />
                </div>
              </transition>

              <div class="divider"></div>

              <div class="toggle-row">
                <div>
                  <span class="toggle-label">🟡 Нужен судья</span>
                  <p class="toggle-desc">Можно добавить судью отдельно</p>
                </div>
                <label class="switch">
                  <input v-model="form.requires_referee" type="checkbox" />
                  <span class="slider"></span>
                </label>
              </div>
            </div>
          </div>

          <!-- Status (organizer can change) -->
          <div class="card" style="margin-top: 12px;">
            <div class="card-body">
              <h3 class="form-section-title">Статус матча</h3>
              <div class="status-grid">
                <button
                  v-for="s in statuses"
                  :key="s.value"
                  type="button"
                  :class="['status-btn', { active: form.status === s.value }]"
                  @click="form.status = s.value"
                >
                  {{ s.label }}
                </button>
              </div>
            </div>
          </div>

          <!-- Error -->
          <div v-if="saveError" class="alert alert-error" style="margin-top: 12px;">{{ saveError }}</div>

          <!-- Submit -->
          <button
            type="submit"
            class="btn btn-primary btn-full"
            style="margin-top: 16px;"
            :disabled="saving"
          >
            {{ saving ? 'Сохранение...' : '💾 Сохранить изменения' }}
          </button>
        </form>
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
const loadError = ref('')
const saving = ref(false)
const saveError = ref('')
const success = ref(false)

const statuses = [
  { value: 'upcoming', label: '📅 Предстоящий' },
  { value: 'ongoing',  label: '🟢 Идёт' },
  { value: 'finished', label: '✅ Завершён' },
  { value: 'cancelled', label: '❌ Отменён' },
]

const form = ref({
  title: '',
  address: '',
  match_date: '',
  max_players: 10,
  description: '',
  visibility: 'public',
  is_paid: false,
  price_per_player: 0,
  requires_referee: false,
  status: 'upcoming',
})

function toLocalDatetime(isoStr) {
  // Keep as-is up to minutes — the DB stores naive UTC, no conversion needed
  return isoStr ? isoStr.slice(0, 16) : ''
}

onMounted(async () => {
  try {
    const res = await matchesApi.get(route.params.id)
    const m = res.data
    form.value = {
      title:            m.title,
      address:          m.address,
      match_date:       toLocalDatetime(m.match_date),
      max_players:      m.max_players,
      description:      m.description || '',
      visibility:       m.visibility,
      is_paid:          m.is_paid,
      price_per_player: m.price_per_player,
      requires_referee: m.requires_referee,
      status:           m.status,
    }
  } catch (e) {
    loadError.value = e.message
  } finally {
    loading.value = false
  }
})

async function submit() {
  saving.value = true
  saveError.value = ''
  success.value = false
  try {
    const payload = {
      ...form.value,
      match_date: new Date(form.value.match_date).toISOString(),
      description: form.value.description || null,
      price_per_player: form.value.is_paid ? form.value.price_per_player : 0,
    }
    await matchesApi.update(route.params.id, payload)
    success.value = true
    window.scrollTo({ top: 0, behavior: 'smooth' })
    setTimeout(() => router.push(`/matches/${route.params.id}`), 1500)
  } catch (e) {
    saveError.value = e.message
  } finally {
    saving.value = false
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
.form-row { display: flex; gap: 10px; }
.form-group--half { flex: 1; }

.toggle-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.toggle-label { font-size: 15px; font-weight: 600; }
.toggle-desc { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

.seg-control { display: flex; border-radius: var(--radius); overflow: hidden; border: 1.5px solid var(--border); }
.seg-btn {
  padding: 7px 12px; background: none; border: none; color: var(--text-muted);
  font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.seg-btn.active { background: var(--accent-glow); color: var(--accent); }

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

.status-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.status-btn {
  padding: 10px; border-radius: var(--radius); border: 1.5px solid var(--border);
  background: var(--bg-secondary); color: var(--text-secondary);
  font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.status-btn.active {
  border-color: var(--accent); background: var(--accent-glow); color: var(--accent);
}

.slide-up-enter-active, .slide-up-leave-active { transition: all 0.25s ease; }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
