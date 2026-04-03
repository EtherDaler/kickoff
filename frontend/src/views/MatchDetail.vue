<template>
  <div class="page">
    <header class="page-header">
      <button class="back-btn" @click="$router.back()">←</button>
      <h1>{{ match?.title || 'Матч' }}</h1>
      <div style="width: 40px;"></div>
    </header>

    <div class="page-content">
      <div v-if="loading" class="loading-center"><div class="spinner"></div></div>
      <div v-else-if="error" class="alert alert-error">{{ error }}</div>

      <template v-else-if="match">
        <!-- Status banner -->
        <div :class="['status-banner', `status-${match.status}`]">
          <span>{{ statusLabels[match.status] }}</span>
          <span class="badge" :class="visBadge">{{ match.visibility === 'public' ? '🌍 Публичный' : '🔒 Закрытый' }}</span>
        </div>

        <!-- Info card -->
        <div class="card" style="margin-top: 12px;">
          <div class="card-body">
            <div class="info-rows">
              <div class="info-row">
                <span class="info-icon">📍</span>
                <span>{{ match.address }}</span>
              </div>
              <div class="info-row">
                <span class="info-icon">📅</span>
                <span>{{ formatDate(match.match_date) }}</span>
              </div>
              <div class="info-row">
                <span class="info-icon">👥</span>
                <span>{{ confirmedCount }}/{{ match.max_players }} игроков</span>
                <div class="mini-progress">
                  <div class="mini-progress-fill" :style="{ width: progressPct + '%' }"></div>
                </div>
              </div>
              <div class="info-row">
                <span class="info-icon">💰</span>
                <span v-if="match.is_paid">{{ match.price_per_player }} ₽ / чел.</span>
                <span v-else>Бесплатно</span>
              </div>
              <div v-if="match.description" class="info-row">
                <span class="info-icon">📝</span>
                <span>{{ match.description }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Action buttons -->
        <div class="actions-block" style="margin-top: 12px;">
          <template v-if="!isOrganizer && !isParticipant && match.status === 'upcoming'">
            <button class="btn btn-primary btn-full" :disabled="actionLoading" @click="joinAsPlayer">
              ✅ Присоединиться
            </button>
            <button
              v-if="match.requires_referee"
              class="btn btn-outline btn-full"
              style="margin-top: 8px;"
              :disabled="actionLoading"
              @click="joinAsReferee"
            >
              🟡 Судья
            </button>
          </template>

          <template v-if="isParticipant && !isOrganizer">
            <div v-if="myParticipation?.status === 'invited'" class="alert alert-info">
              📨 Тебя пригласили на этот матч
              <button class="btn btn-primary btn-sm" style="margin-top: 8px;" @click="acceptInvite">Принять</button>
            </div>

            <div v-else-if="myParticipation?.status === 'pending_payment' && match.is_paid" class="receipt-block card">
              <div class="card-body">
                <p class="alert alert-info" style="margin:0 0 10px;">⏳ Загрузи чек для подтверждения участия</p>
                <input ref="fileInput" type="file" accept="image/*" style="display:none;" @change="uploadReceipt" />
                <button class="btn btn-primary btn-full" :disabled="uploadLoading" @click="$refs.fileInput.click()">
                  {{ uploadLoading ? 'Загрузка...' : '📸 Загрузить чек' }}
                </button>
              </div>
            </div>

            <button
              v-if="['confirmed', 'pending_payment'].includes(myParticipation?.status)"
              class="btn btn-danger btn-full"
              :disabled="actionLoading"
              @click="leave"
            >
              ❌ Отменить участие
            </button>
          </template>

          <template v-if="canEdit">
            <button
              v-if="match.status === 'upcoming'"
              class="btn btn-primary btn-full"
              @click="$router.push(`/matches/${match.id}/edit`)"
            >
              ✏️ Редактировать матч
            </button>
            <template v-if="isOrganizer">
              <button
                v-if="match.status === 'finished'"
                class="btn btn-secondary btn-full"
                style="margin-top: 8px;"
                @click="$router.push(`/matches/${match.id}/stats`)"
              >
                📊 Заполнить статистику
              </button>
              <button
                v-else-if="match.status === 'upcoming'"
                class="btn btn-outline btn-full"
                style="margin-top: 8px;"
                @click="$router.push(`/matches/${match.id}/stats`)"
              >
                📊 Управление матчем
              </button>
            </template>
          </template>
        </div>

        <!-- Alert -->
        <div v-if="actionError" class="alert alert-error" style="margin-top: 8px;">{{ actionError }}</div>

        <!-- Receipts block (organizer/co-org only, paid matches) -->
        <div v-if="canEdit && match.is_paid" style="margin-top: 16px;">
          <h3 class="section-title">🧾 Квитанции об оплате</h3>
          <div v-if="receiptsLoading" class="loading-center"><div class="spinner"></div></div>
          <div v-else-if="!receipts.length" class="empty-hint">Квитанции ещё не загружены</div>
          <div v-else class="receipts-list">
            <div v-for="r in receipts" :key="r.id" class="receipt-item card">
              <div class="card-body">
                <div class="receipt-header">
                  <span class="receipt-name">{{ r.user.first_name }} {{ r.user.last_name || '' }}</span>
                  <span :class="['badge', receiptStatusBadge(r.status)]">{{ receiptStatusLabel(r.status) }}</span>
                </div>
                <a :href="r.receipt_url" target="_blank" class="receipt-link">📎 Открыть квитанцию</a>
                <div v-if="r.status === 'uploaded'" class="receipt-actions">
                  <button class="btn btn-primary btn-sm" :disabled="receiptsLoading" @click="reviewReceipt(r.id, 'approved')">
                    ✅ Допустить
                  </button>
                  <button class="btn btn-danger btn-sm" :disabled="receiptsLoading" @click="reviewReceipt(r.id, 'rejected')">
                    ❌ Отклонить
                  </button>
                </div>
                <div v-else-if="r.status === 'approved'" class="receipt-ok-hint">Участник допущен к матчу</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Participants -->
        <div style="margin-top: 16px;">
          <h3 class="section-title">
            Участники
            <span class="badge badge-blue" style="margin-left: 6px;">{{ confirmedCount }}/{{ match.max_players }}</span>
          </h3>

          <div class="participants-list">
            <div
              v-for="p in match.participants"
              :key="p.id"
              :class="['participant-item', `status-${p.status}`]"
            >
              <div class="participant-avatar">
                <img v-if="p.user.avatar_url" :src="p.user.avatar_url" class="avatar" width="40" height="40" />
                <div v-else class="avatar-placeholder" style="width:40px;height:40px;font-size:16px;">
                  {{ p.user.first_name[0] }}
                </div>
              </div>
              <div class="participant-info">
                <span class="participant-name">
                  {{ p.user.first_name }} {{ p.user.last_name || '' }}
                  <span v-if="p.user.id === match.organizer.id" class="badge badge-orange" style="margin-left:4px;">Орг.</span>
                  <span v-else-if="p.is_co_organizer" class="badge badge-orange" style="margin-left:4px;">Соорг.</span>
                  <span v-if="p.role === 'referee'" class="badge badge-yellow" style="margin-left:4px;">Судья</span>
                </span>
                <span v-if="p.user.username" class="participant-username">@{{ p.user.username }}</span>
              </div>
              <div class="participant-status" style="display:flex;align-items:center;gap:6px;flex-shrink:0;">
                <span :class="['badge', participantStatusBadge(p.status)]">
                  {{ participantStatusLabel(p.status) }}
                </span>
                <!-- Controls visible only to organizer for non-organizer participants -->
                <template v-if="canEdit && p.user.id !== match.organizer.id">
                  <!-- Co-organizer toggle (main organizer only) -->
                  <button
                    v-if="isOrganizer && !['cancelled','rejected'].includes(p.status)"
                    class="btn-icon"
                    :title="p.is_co_organizer ? 'Снять соорганизатора' : 'Назначить соорганизатором'"
                    :disabled="coOrgLoading"
                    @click="toggleCoOrganizer(p)"
                  >{{ p.is_co_organizer ? '👑✕' : '👑' }}</button>
                  <!-- Kick button -->
                  <button
                    v-if="!['cancelled','rejected'].includes(p.status)"
                    class="btn-icon btn-icon--danger"
                    title="Исключить участника"
                    :disabled="kickLoading"
                    @click="kickParticipant(p)"
                  >✕</button>
                </template>
              </div>
            </div>
          </div>
        </div>

        <!-- Match Stats -->
        <div v-if="stats" style="margin-top: 16px;">
          <h3 class="section-title">📊 Итоговая статистика</h3>
          <div class="score-banner">
            <span class="score">{{ stats.team1_score }}</span>
            <span class="score-sep">:</span>
            <span class="score">{{ stats.team2_score }}</span>
          </div>
          <div v-for="ps in stats.player_stats" :key="ps.id" class="stat-row card">
            <div class="card-body">
              <div class="stat-row-header">
                <span class="stat-player-name">{{ ps.user.first_name }} {{ ps.user.last_name || '' }}</span>
                <span v-if="ps.is_referee" class="badge badge-yellow">Судья</span>
              </div>
              <div v-if="!ps.is_referee" class="stat-chips-row">
                <div v-if="ps.goals" class="mini-stat">⚽ {{ ps.goals }}</div>
                <div v-if="ps.assists" class="mini-stat">🎯 {{ ps.assists }}</div>
                <div v-if="ps.yellow_cards" class="mini-stat">🟡 {{ ps.yellow_cards }}</div>
                <div v-if="ps.red_cards" class="mini-stat">🔴 {{ ps.red_cards }}</div>
                <div v-if="ps.is_injured" class="mini-stat">🏥 Травма</div>
              </div>
              <p v-if="ps.notes" style="font-size:13px;color:var(--text-secondary);margin-top:4px;">{{ ps.notes }}</p>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { matchesApi } from '@/api'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const match = ref(null)
const stats = ref(null)
const loading = ref(true)
const error = ref('')
const actionLoading = ref(false)
const actionError = ref('')
const uploadLoading = ref(false)
const receipts = ref([])
const receiptsLoading = ref(false)
const coOrgLoading = ref(false)
const kickLoading = ref(false)

const me = computed(() => authStore.user)
const isOrganizer = computed(() => me.value && match.value?.organizer?.id === me.value.id)
const isCoOrganizer = computed(() =>
  match.value?.participants?.some(p => p.user.id === me.value?.id && p.is_co_organizer)
)
const canEdit = computed(() => isOrganizer.value || isCoOrganizer.value)
const isParticipant = computed(() => match.value?.participants?.some(p => p.user.id === me.value?.id))
const myParticipation = computed(() => match.value?.participants?.find(p => p.user.id === me.value?.id))
const confirmedCount = computed(() => match.value?.participants?.filter(p => p.status === 'confirmed').length || 0)
const progressPct = computed(() => Math.min(100, (confirmedCount.value / (match.value?.max_players || 1)) * 100))
const visBadge = computed(() => match.value?.visibility === 'public' ? 'badge-blue' : 'badge-gray')

const statusLabels = {
  upcoming: '📅 Предстоящий матч',
  ongoing: '🟢 Матч идёт',
  finished: '✅ Матч завершён',
  cancelled: '❌ Матч отменён',
}

async function loadMatch() {
  loading.value = true
  error.value = ''
  try {
    const res = await matchesApi.get(route.params.id)
    match.value = res.data
    try {
      const sr = await matchesApi.getStats(route.params.id)
      stats.value = sr.data
    } catch { stats.value = null }
    // Auto-load receipts for organizer/co-org on paid matches
    if (res.data.is_paid) {
      const myId = authStore.user?.id
      const amOrg = res.data.organizer?.id === myId
      const amCoOrg = res.data.participants?.some(p => p.user.id === myId && p.is_co_organizer)
      if (amOrg || amCoOrg) {
        try {
          const rr = await matchesApi.getReceipts(route.params.id)
          receipts.value = rr.data
        } catch { receipts.value = [] }
      }
    }
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function joinAsPlayer() {
  actionLoading.value = true
  actionError.value = ''
  try {
    const res = await matchesApi.join(route.params.id, false)
    match.value = res.data
  } catch (e) { actionError.value = e.message }
  finally { actionLoading.value = false }
}

async function joinAsReferee() {
  actionLoading.value = true
  actionError.value = ''
  try {
    const res = await matchesApi.join(route.params.id, true)
    match.value = res.data
  } catch (e) { actionError.value = e.message }
  finally { actionLoading.value = false }
}

async function leave() {
  actionLoading.value = true
  actionError.value = ''
  try {
    const res = await matchesApi.leave(route.params.id)
    match.value = res.data
  } catch (e) { actionError.value = e.message }
  finally { actionLoading.value = false }
}

async function acceptInvite() {
  actionLoading.value = true
  try {
    const res = await matchesApi.acceptInvite(route.params.id)
    match.value = res.data
  } catch (e) { actionError.value = e.message }
  finally { actionLoading.value = false }
}

async function uploadReceipt(event) {
  const file = event.target.files[0]
  if (!file) return
  uploadLoading.value = true
  try {
    await matchesApi.uploadReceipt(route.params.id, file)
    await loadMatch()
  } catch (e) { actionError.value = e.message }
  finally { uploadLoading.value = false }
}

async function reviewReceipt(receiptId, status) {
  receiptsLoading.value = true
  try {
    await matchesApi.reviewReceipt(route.params.id, receiptId, { status })
    const res = await matchesApi.getReceipts(route.params.id)
    receipts.value = res.data
    await loadMatch()
  } catch (e) { actionError.value = e.message }
  finally { receiptsLoading.value = false }
}

async function kickParticipant(p) {
  if (!confirm(`Исключить ${p.user.first_name} из матча?`)) return
  kickLoading.value = true
  actionError.value = ''
  try {
    const res = await matchesApi.kickParticipant(match.value.id, p.user.id)
    match.value = res.data
  } catch (e) { actionError.value = e.message }
  finally { kickLoading.value = false }
}

function formatDate(dt) {
  return new Date(dt).toLocaleString('ru-RU', {
    day: '2-digit', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

async function toggleCoOrganizer(p) {
  coOrgLoading.value = true
  actionError.value = ''
  try {
    const fn = p.is_co_organizer ? matchesApi.revokeCoOrganizer : matchesApi.grantCoOrganizer
    const res = await fn(match.value.id, p.user.id)
    match.value = res.data
  } catch (e) { actionError.value = e.message }
  finally { coOrgLoading.value = false }
}

const participantStatusLabel = (s) => ({ confirmed: 'Подтверждён', pending_payment: 'Ожидает оплаты', invited: 'Приглашён', cancelled: 'Отменён', rejected: 'Отклонён' }[s] || s)
const participantStatusBadge = (s) => ({ confirmed: 'badge-green', pending_payment: 'badge-yellow', invited: 'badge-blue', cancelled: 'badge-gray', rejected: 'badge-red' }[s] || 'badge-gray')
const receiptStatusLabel = (s) => ({ uploaded: 'Загружен', approved: 'Принят', rejected: 'Отклонён', refunded: 'Возврат' }[s] || s)
const receiptStatusBadge = (s) => ({ uploaded: 'badge-yellow', approved: 'badge-green', rejected: 'badge-red', refunded: 'badge-blue' }[s] || 'badge-gray')

onMounted(loadMatch)
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

.status-banner {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px;
  border-radius: var(--radius);
  font-weight: 600; font-size: 15px;
}
.status-upcoming { background: rgba(96, 165, 250, 0.1); color: var(--info); }
.status-ongoing { background: rgba(74, 222, 128, 0.1); color: var(--accent); }
.status-finished { background: rgba(148, 163, 184, 0.1); color: var(--text-secondary); }
.status-cancelled { background: rgba(248, 113, 113, 0.1); color: var(--danger); }

.info-rows { display: flex; flex-direction: column; gap: 10px; }
.info-row { display: flex; align-items: flex-start; gap: 10px; font-size: 14px; }
.info-icon { font-size: 16px; flex-shrink: 0; margin-top: 1px; }
.mini-progress {
  flex: 1; height: 4px; background: var(--border);
  border-radius: 2px; margin-left: 8px; align-self: center;
}
.mini-progress-fill { height: 100%; background: var(--accent); border-radius: 2px; }

.actions-block { display: flex; flex-direction: column; gap: 8px; }
.receipt-block { margin-top: 0; }

.section-title { font-size: 16px; font-weight: 700; margin-bottom: 12px; display: flex; align-items: center; }

.participants-list { display: flex; flex-direction: column; gap: 8px; }
.participant-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px;
  background: var(--bg-card); border-radius: var(--radius);
  border: 1px solid var(--border);
}
.participant-item.status-cancelled { opacity: 0.5; }
.participant-info { flex: 1; display: flex; flex-direction: column; }
.participant-name { font-size: 14px; font-weight: 600; }
.participant-username { font-size: 12px; color: var(--text-muted); }

.score-banner {
  display: flex; align-items: center; justify-content: center; gap: 16px;
  padding: 20px; background: var(--bg-card);
  border-radius: var(--radius-lg); border: 1px solid var(--border);
  margin-bottom: 12px;
}
.score { font-size: 48px; font-weight: 900; color: var(--accent); }
.score-sep { font-size: 32px; color: var(--text-secondary); }

.stat-row { margin-bottom: 8px; }
.stat-row-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.stat-player-name { font-weight: 600; font-size: 14px; }
.stat-chips-row { display: flex; flex-wrap: wrap; gap: 8px; }
.mini-stat {
  padding: 4px 10px; border-radius: 20px;
  background: var(--bg-secondary); font-size: 13px; font-weight: 600;
}

.receipts-list { margin-top: 10px; display: flex; flex-direction: column; gap: 8px; }
.receipt-item { }
.receipt-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-weight: 600; }
.receipt-link { color: var(--info); font-size: 14px; display: block; margin-bottom: 8px; }
.receipt-actions { display: flex; gap: 8px; }

.badge-orange { background: rgba(251, 146, 60, 0.15); color: #f97316; }

.btn-icon {
  background: none; border: 1px solid var(--border);
  border-radius: 8px; padding: 2px 7px; cursor: pointer;
  font-size: 12px; color: var(--text-secondary);
  transition: background 0.15s;
  flex-shrink: 0;
  line-height: 1.6;
}
.btn-icon:hover:not(:disabled) { background: var(--bg-secondary); }
.btn-icon:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-icon--danger { border-color: rgba(248,113,113,0.4); color: var(--danger); }
.btn-icon--danger:hover:not(:disabled) { background: rgba(248,113,113,0.1); }

.empty-hint { font-size: 13px; color: var(--text-muted); text-align: center; padding: 12px 0; }
.receipt-name { font-weight: 600; font-size: 14px; }
.receipt-ok-hint { font-size: 12px; color: var(--accent); margin-top: 4px; }
</style>
