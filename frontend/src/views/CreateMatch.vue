<template>
  <div class="page">
    <header class="page-header">
      <button class="back-btn" @click="$router.back()">←</button>
      <h1>Создать матч</h1>
      <div style="width: 40px;"></div>
    </header>

    <div class="page-content">
      <div v-if="success" class="alert alert-success">
        ✅ Матч создан!
        <router-link :to="`/matches/${createdId}`" style="color: inherit; font-weight: 700;"> Открыть →</router-link>
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
              <textarea v-model="form.description" class="form-input" placeholder="Дополнительная информация..." rows="3"></textarea>
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
                <input v-model.number="form.price_per_player" type="number" class="form-input" min="0" step="50" />
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

        <!-- Error -->
        <div v-if="error" class="alert alert-error" style="margin-top: 12px;">{{ error }}</div>

        <!-- Submit -->
        <button
          type="submit"
          class="btn btn-primary btn-full"
          style="margin-top: 16px;"
          :disabled="loading"
        >
          {{ loading ? 'Создание...' : '⚽ Создать матч' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { matchesApi } from '@/api'

const router = useRouter()

const loading = ref(false)
const error = ref('')
const success = ref(false)
const createdId = ref(null)

const defaultDate = () => {
  const d = new Date()
  d.setHours(d.getHours() + 24)
  return d.toISOString().slice(0, 16)
}

const form = ref({
  title: '',
  address: '',
  match_date: defaultDate(),
  max_players: 10,
  description: '',
  visibility: 'public',
  is_paid: false,
  price_per_player: 0,
  requires_referee: false,
  invited_user_ids: [],
})

async function submit() {
  loading.value = true
  error.value = ''
  try {
    const payload = {
      ...form.value,
      match_date: new Date(form.value.match_date).toISOString(),
    }
    const res = await matchesApi.create(payload)
    createdId.value = res.data.id
    success.value = true
    setTimeout(() => router.push(`/matches/${res.data.id}`), 1200)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
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

/* Toggle switch */
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
