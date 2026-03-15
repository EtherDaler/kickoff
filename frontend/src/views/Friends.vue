<template>
  <div class="page">
    <header class="page-header">
      <h1>👥 Друзья</h1>
      <span v-if="pendingCount" class="badge badge-red">{{ pendingCount }}</span>
    </header>

    <div class="page-content">
      <!-- Search users -->
      <div class="search-bar">
        <span class="search-icon">🔍</span>
        <input
          v-model="searchQ"
          class="search-input"
          placeholder="Найти пользователя..."
          @input="onSearch"
        />
        <button v-if="searchQ" class="search-clear" @click="clearSearch">✕</button>
      </div>

      <!-- Search results -->
      <transition name="slide-up">
        <div v-if="searchQ && searchResults.length" class="section-block">
          <h3 class="section-title">Результаты поиска</h3>
          <div v-for="u in searchResults" :key="u.id" class="user-card card">
            <div class="card-body">
              <div class="user-card-row">
                <div class="user-info-left">
                  <img v-if="u.avatar_url" :src="u.avatar_url" class="avatar" width="44" height="44" />
                  <div v-else class="avatar-placeholder" style="width:44px;height:44px;font-size:18px;">{{ u.first_name[0] }}</div>
                  <div>
                    <p class="user-name">{{ u.first_name }} {{ u.last_name || '' }}</p>
                    <p v-if="u.username" class="user-username">@{{ u.username }}</p>
                    <div v-if="u.roles?.length" class="user-roles">
                      <span v-for="r in u.roles" :key="r" class="role-tag" style="font-size:11px;">{{ roleNames[r] }}</span>
                    </div>
                  </div>
                </div>
                <button
                  class="btn btn-outline btn-sm"
                  :disabled="sentIds.has(u.telegram_id)"
                  @click="sendRequest(u)"
                >
                  {{ sentIds.has(u.telegram_id) ? '✅ Отправлено' : '➕' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </transition>

      <!-- Tabs -->
      <div class="tabs" style="margin-bottom: 14px;">
        <button :class="['tab-btn', { active: activeTab === 'requests' }]" @click="activeTab = 'requests'">
          📨 Запросы
          <span v-if="pendingCount" class="tab-badge">{{ pendingCount }}</span>
        </button>
        <button :class="['tab-btn', { active: activeTab === 'friends' }]" @click="activeTab = 'friends'">
          👥 Друзья
        </button>
      </div>

      <!-- Friend Requests -->
      <div v-if="activeTab === 'requests'">
        <div v-if="requestsLoading" class="loading-center"><div class="spinner"></div></div>
        <div v-else-if="!friendRequests.length" class="empty-state">
          <span class="icon">📨</span>
          <h3>Нет запросов</h3>
          <p>Входящих запросов в друзья нет</p>
        </div>
        <div v-else v-for="req in friendRequests" :key="req.id" class="user-card card">
          <div class="card-body">
            <div class="user-card-row">
              <div class="user-info-left">
                <img v-if="req.sender.avatar_url" :src="req.sender.avatar_url" class="avatar" width="44" height="44" />
                <div v-else class="avatar-placeholder" style="width:44px;height:44px;font-size:18px;">{{ req.sender.first_name[0] }}</div>
                <div>
                  <p class="user-name">{{ req.sender.first_name }} {{ req.sender.last_name || '' }}</p>
                  <p v-if="req.sender.username" class="user-username">@{{ req.sender.username }}</p>
                </div>
              </div>
              <div class="request-actions">
                <button class="btn btn-primary btn-sm" @click="accept(req.id)">✅</button>
                <button class="btn btn-danger btn-sm" @click="decline(req.id)">❌</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Friends List -->
      <div v-if="activeTab === 'friends'">
        <div v-if="friendsLoading" class="loading-center"><div class="spinner"></div></div>
        <div v-else-if="!friends.length" class="empty-state">
          <span class="icon">👥</span>
          <h3>Нет друзей</h3>
          <p>Найди пользователей и добавь их в друзья</p>
        </div>
        <div v-else v-for="u in friends" :key="u.id" class="user-card card">
          <div class="card-body">
            <div class="user-card-row">
              <div class="user-info-left">
                <img v-if="u.avatar_url" :src="u.avatar_url" class="avatar" width="44" height="44" />
                <div v-else class="avatar-placeholder" style="width:44px;height:44px;font-size:18px;">{{ u.first_name[0] }}</div>
                <div>
                  <p class="user-name">{{ u.first_name }} {{ u.last_name || '' }}</p>
                  <p v-if="u.username" class="user-username">@{{ u.username }}</p>
                  <div v-if="u.roles?.length" class="user-roles">
                    <span v-for="r in u.roles" :key="r" class="role-tag" style="font-size:11px;">{{ roleNames[r] }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usersApi } from '@/api'

const roleNames = {
  forward: '⚡ Нападающий',
  midfielder: '🔄 Полузащитник',
  defender: '🛡 Защитник',
  goalkeeper: '🧤 Вратарь',
  referee: '🟡 Судья',
}

const activeTab = ref('requests')
const friendRequests = ref([])
const friends = ref([])
const requestsLoading = ref(false)
const friendsLoading = ref(false)
const searchQ = ref('')
const searchResults = ref([])
const sentIds = ref(new Set())

const pendingCount = computed(() => friendRequests.value.length)

let searchTimeout = null
function onSearch() {
  clearTimeout(searchTimeout)
  if (!searchQ.value.trim()) { searchResults.value = []; return }
  searchTimeout = setTimeout(async () => {
    try {
      const res = await usersApi.search(searchQ.value)
      searchResults.value = res.data
    } catch { searchResults.value = [] }
  }, 400)
}

function clearSearch() {
  searchQ.value = ''
  searchResults.value = []
}

async function sendRequest(user) {
  try {
    await usersApi.sendFriendRequest(user.telegram_id)
    sentIds.value.add(user.telegram_id)
  } catch { }
}

async function accept(id) {
  await usersApi.acceptFriendRequest(id)
  friendRequests.value = friendRequests.value.filter(r => r.id !== id)
  await loadFriends()
}

async function decline(id) {
  await usersApi.declineFriendRequest(id)
  friendRequests.value = friendRequests.value.filter(r => r.id !== id)
}

async function loadRequests() {
  requestsLoading.value = true
  try {
    const res = await usersApi.getFriendRequests()
    friendRequests.value = res.data
  } finally { requestsLoading.value = false }
}

async function loadFriends() {
  friendsLoading.value = true
  try {
    const res = await usersApi.getFriends()
    friends.value = res.data
  } finally { friendsLoading.value = false }
}

onMounted(async () => {
  await Promise.all([loadRequests(), loadFriends()])
})
</script>

<style scoped>
.tabs { display: flex; gap: 8px; }
.tab-btn {
  flex: 1; padding: 9px 12px;
  border-radius: var(--radius); border: 1.5px solid var(--border);
  background: transparent; color: var(--text-secondary);
  font-size: 13px; font-weight: 600; cursor: pointer;
  transition: all 0.2s; display: flex; align-items: center;
  justify-content: center; gap: 6px;
}
.tab-btn.active { background: var(--accent-glow); border-color: var(--border-accent); color: var(--accent); }
.tab-badge {
  background: var(--danger); color: white; border-radius: 10px;
  padding: 1px 6px; font-size: 11px;
}

.search-bar {
  display: flex; align-items: center;
  background: var(--bg-card); border: 1.5px solid var(--border);
  border-radius: var(--radius); padding: 0 12px; margin-bottom: 14px; gap: 8px;
}
.search-icon { font-size: 16px; color: var(--text-muted); }
.search-input {
  flex: 1; background: none; border: none; outline: none;
  color: var(--text-primary); font-size: 15px; padding: 12px 0; font-family: inherit;
}
.search-input::placeholder { color: var(--text-muted); }
.search-clear { background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 16px; padding: 4px; }

.user-card { margin-bottom: 8px; }
.user-card-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.user-info-left { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; }
.user-name { font-size: 15px; font-weight: 600; }
.user-username { font-size: 13px; color: var(--text-muted); }
.user-roles { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
.request-actions { display: flex; gap: 6px; }
.section-title { font-size: 15px; font-weight: 700; margin-bottom: 10px; }
.section-block { margin-bottom: 16px; }
</style>
