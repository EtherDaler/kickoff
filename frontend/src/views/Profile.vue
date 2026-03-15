<template>
  <div class="page profile-page">
    <header class="page-header">
      <h1>Мой профиль</h1>
      <button class="btn btn-sm btn-outline" @click="showEdit = !showEdit">
        {{ showEdit ? 'Готово' : '✏️ Изменить' }}
      </button>
    </header>

    <div class="page-content">
      <div v-if="!user" class="loading-center"><div class="spinner"></div></div>

      <template v-else>
        <!-- Avatar + Name -->
        <div class="profile-hero card">
          <div class="card-body">
            <div class="profile-hero__top">
              <div class="profile-avatar-wrap">
                <img v-if="user.avatar_url" :src="user.avatar_url" class="avatar" width="72" height="72" />
                <div v-else class="avatar-placeholder" style="width:72px;height:72px;font-size:28px;">
                  {{ user.first_name[0] }}
                </div>
              </div>
              <div class="profile-hero__info">
                <h2 class="profile-name">{{ user.first_name }} {{ user.last_name || '' }}</h2>
                <p v-if="user.username" class="profile-username">@{{ user.username }}</p>
                <div class="profile-meta">
                  <span v-if="user.age">🎂 {{ user.age }} лет</span>
                  <span v-if="user.city">🏙 {{ user.city }}</span>
                </div>
              </div>
            </div>
            <p v-if="user.bio" class="profile-bio">{{ user.bio }}</p>
            <div v-if="user.roles?.length" class="profile-roles">
              <span v-for="r in user.roles" :key="r" class="role-tag">{{ roleNames[r] || r }}</span>
            </div>
          </div>
        </div>

        <!-- Edit Form -->
        <transition name="slide-up">
          <div v-if="showEdit" class="card" style="margin-top:12px;">
            <div class="card-body">
              <h3 class="section-title">Редактировать профиль</h3>
              <div class="form-group">
                <label class="form-label">Возраст</label>
                <input v-model.number="form.age" type="number" class="form-input" placeholder="25" min="5" max="100" />
              </div>
              <div class="form-group">
                <label class="form-label">Город</label>
                <input v-model="form.city" class="form-input" placeholder="Москва" />
              </div>
              <div class="form-group">
                <label class="form-label">О себе</label>
                <textarea v-model="form.bio" class="form-input" placeholder="Расскажи о себе..." rows="3"></textarea>
              </div>
              <div class="form-group">
                <label class="form-label">Позиции</label>
                <div class="roles-grid">
                  <button
                    v-for="(name, key) in roleNames"
                    :key="key"
                    :class="['role-btn', { active: form.roles.includes(key) }]"
                    @click="toggleRole(key)"
                  >{{ name }}</button>
                </div>
              </div>
              <div v-if="saveError" class="alert alert-error">{{ saveError }}</div>
              <button class="btn btn-primary btn-full" :disabled="saving" @click="saveProfile">
                {{ saving ? 'Сохранение...' : '💾 Сохранить' }}
              </button>
            </div>
          </div>
        </transition>

        <!-- Stats -->
        <div v-if="user.stats" class="section-block" style="margin-top:16px;">
          <h3 class="section-title">📊 Статистика</h3>
          <div class="stats-grid">
            <div class="stat-chip">
              <span class="value">{{ user.stats.total_matches }}</span>
              <span class="label">Матчей</span>
            </div>
            <div class="stat-chip">
              <span class="value">{{ user.stats.total_goals }}</span>
              <span class="label">Голов</span>
            </div>
            <div class="stat-chip">
              <span class="value">{{ user.stats.total_assists }}</span>
              <span class="label">Передач</span>
            </div>
            <div class="stat-chip">
              <span class="value">{{ user.stats.total_yellow_cards }}</span>
              <span class="label">Ж.карт</span>
            </div>
            <div class="stat-chip">
              <span class="value">{{ user.stats.total_red_cards }}</span>
              <span class="label">К.карт</span>
            </div>
            <div class="stat-chip">
              <span class="value">{{ user.stats.referee_matches }}</span>
              <span class="label">Судейств</span>
            </div>
          </div>
        </div>

        <!-- My Matches -->
        <div class="section-block" style="margin-top:16px;">
          <h3 class="section-title">⚽ Мои матчи</h3>
          <div v-if="loadingMatches" class="loading-center"><div class="spinner"></div></div>
          <template v-else-if="myMatches.length">
            <MatchCard v-for="m in myMatches" :key="m.id" :match="m" style="margin-bottom:10px;" />
          </template>
          <div v-else class="empty-state">
            <span class="icon">⚽</span>
            <p>У тебя пока нет матчей</p>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useMatchesStore } from '@/stores/matches'
import MatchCard from '@/components/MatchCard.vue'

const authStore = useAuthStore()
const matchesStore = useMatchesStore()

const user = computed(() => authStore.user)
const myMatches = computed(() => matchesStore.myMatches)
const loadingMatches = ref(false)

const showEdit = ref(false)
const saving = ref(false)
const saveError = ref('')

const roleNames = {
  forward: '⚡ Нападающий',
  midfielder: '🔄 Полузащитник',
  defender: '🛡 Защитник',
  goalkeeper: '🧤 Вратарь',
  referee: '🟡 Судья',
}

const form = ref({ age: null, city: '', bio: '', roles: [] })

watch(user, (u) => {
  if (u) {
    form.value = {
      age: u.age || null,
      city: u.city || '',
      bio: u.bio || '',
      roles: [...(u.roles || [])],
    }
  }
}, { immediate: true })

function toggleRole(key) {
  const idx = form.value.roles.indexOf(key)
  if (idx >= 0) form.value.roles.splice(idx, 1)
  else form.value.roles.push(key)
}

async function saveProfile() {
  saving.value = true
  saveError.value = ''
  try {
    await authStore.updateProfile({
      age: form.value.age || null,
      city: form.value.city || null,
      bio: form.value.bio || null,
      roles: form.value.roles,
    })
    showEdit.value = false
  } catch (e) {
    saveError.value = e.message
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await authStore.refreshMe()
  loadingMatches.value = true
  await matchesStore.fetchMyMatches()
  loadingMatches.value = false
})
</script>

<style scoped>
.profile-hero__top { display: flex; gap: 16px; align-items: flex-start; margin-bottom: 12px; }
.profile-hero__info { flex: 1; }
.profile-name { font-size: 20px; font-weight: 800; line-height: 1.2; }
.profile-username { color: var(--text-secondary); font-size: 14px; margin-top: 2px; }
.profile-meta { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 6px; font-size: 13px; color: var(--text-secondary); }
.profile-bio { font-size: 14px; color: var(--text-secondary); margin-top: 4px; line-height: 1.5; }
.profile-roles { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }

.section-title { font-size: 16px; font-weight: 700; margin-bottom: 12px; }
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.section-block { }

.roles-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.role-btn {
  padding: 8px 14px;
  border-radius: 20px;
  border: 1.5px solid var(--border);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.role-btn.active {
  border-color: var(--accent);
  background: var(--accent-glow);
  color: var(--accent);
}
</style>
