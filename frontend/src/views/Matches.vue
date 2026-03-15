<template>
  <div class="page">
    <header class="page-header">
      <h1>⚽ Матчи</h1>
      <div class="header-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="['tab-btn', { active: activeTab === tab.key }]"
          @click="switchTab(tab.key)"
        >{{ tab.label }}</button>
      </div>
    </header>

    <div class="page-content">
      <!-- Search -->
      <div class="search-bar">
        <span class="search-icon">🔍</span>
        <input
          v-model="searchQuery"
          class="search-input"
          placeholder="Поиск матчей..."
          @input="onSearch"
        />
        <button v-if="searchQuery" class="search-clear" @click="clearSearch">✕</button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="loading-center"><div class="spinner"></div></div>

      <!-- Empty -->
      <div v-else-if="!filteredMatches.length" class="empty-state">
        <span class="icon">⚽</span>
        <h3>{{ searchQuery ? 'Ничего не найдено' : 'Матчей пока нет' }}</h3>
        <p>{{ searchQuery ? 'Попробуй другой запрос' : 'Создай первый матч!' }}</p>
        <router-link v-if="!searchQuery" to="/matches/create" class="btn btn-primary" style="margin-top: 8px;">
          ➕ Создать матч
        </router-link>
      </div>

      <!-- Matches List -->
      <transition-group v-else name="slide-up" tag="div" class="matches-list">
        <MatchCard
          v-for="match in filteredMatches"
          :key="match.id"
          :match="match"
        />
      </transition-group>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useMatchesStore } from '@/stores/matches'
import { matchesApi } from '@/api'
import MatchCard from '@/components/MatchCard.vue'

const matchesStore = useMatchesStore()

const tabs = [
  { key: 'upcoming', label: 'Все' },
  { key: 'mine', label: 'Мои' },
  { key: 'finished', label: 'История' },
]

const activeTab = ref('upcoming')
const searchQuery = ref('')
const searchResults = ref([])
const isSearching = ref(false)
const loading = ref(false)

const filteredMatches = computed(() => {
  if (searchQuery.value.trim()) return searchResults.value
  if (activeTab.value === 'mine') return matchesStore.myMatches
  return matchesStore.matches
})

let searchTimeout = null
function onSearch() {
  clearTimeout(searchTimeout)
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }
  searchTimeout = setTimeout(async () => {
    try {
      const res = await matchesApi.search(searchQuery.value)
      searchResults.value = res.data
    } catch { searchResults.value = [] }
  }, 400)
}

function clearSearch() {
  searchQuery.value = ''
  searchResults.value = []
}

async function switchTab(key) {
  activeTab.value = key
  await loadMatches()
}

async function loadMatches() {
  loading.value = true
  try {
    if (activeTab.value === 'mine') {
      await matchesStore.fetchMyMatches()
    } else if (activeTab.value === 'finished') {
      await matchesStore.fetchMatches({ status: 'finished' })
    } else {
      await matchesStore.fetchMatches({ status: 'upcoming' })
    }
  } finally {
    loading.value = false
  }
}

onMounted(loadMatches)
</script>

<style scoped>
.page-header { flex-direction: column; height: auto; padding: 12px 16px; gap: 10px; }
.page-header h1 { align-self: flex-start; }

.header-tabs { display: flex; gap: 6px; width: 100%; }
.tab-btn {
  flex: 1;
  padding: 7px 10px;
  border-radius: var(--radius);
  border: 1.5px solid var(--border);
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.tab-btn.active {
  background: var(--accent-glow);
  border-color: var(--border-accent);
  color: var(--accent);
}

.search-bar {
  display: flex;
  align-items: center;
  background: var(--bg-card);
  border: 1.5px solid var(--border);
  border-radius: var(--radius);
  padding: 0 12px;
  margin-bottom: 14px;
  gap: 8px;
}
.search-icon { font-size: 16px; color: var(--text-muted); }
.search-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 15px;
  padding: 12px 0;
  font-family: inherit;
}
.search-input::placeholder { color: var(--text-muted); }
.search-clear {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 16px;
  padding: 4px;
}

.matches-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
</style>
