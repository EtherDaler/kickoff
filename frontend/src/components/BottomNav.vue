<template>
  <nav class="bottom-nav">
    <router-link
      v-for="item in navItems"
      :key="item.path"
      :to="item.path"
      class="nav-item"
      :class="{ active: isActive(item) }"
    >
      <span class="nav-icon">{{ item.icon }}</span>
      <span class="nav-label">{{ item.label }}</span>
    </router-link>
  </nav>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { path: '/matches', icon: '⚽', label: 'Матчи' },
  { path: '/matches/create', icon: '➕', label: 'Создать' },
  { path: '/friends', icon: '👥', label: 'Друзья' },
  { path: '/profile', icon: '👤', label: 'Профиль' },
]

function isActive(item) {
  if (item.path === '/matches') {
    return route.path === '/matches' || (route.path.startsWith('/matches/') && route.path !== '/matches/create')
  }
  return route.path === item.path
}
</script>

<style scoped>
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: var(--nav-height);
  background: var(--bg-secondary);
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-around;
  z-index: 100;
  padding-bottom: env(safe-area-inset-bottom, 0px);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  text-decoration: none;
  color: var(--text-muted);
  flex: 1;
  padding: 8px 4px;
  transition: all 0.2s;
  position: relative;
}

.nav-item.active {
  color: var(--accent);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 32px;
  height: 3px;
  background: var(--accent);
  border-radius: 0 0 4px 4px;
}

.nav-icon {
  font-size: 22px;
  line-height: 1;
  transition: transform 0.2s;
}

.nav-item.active .nav-icon {
  transform: scale(1.15);
}

.nav-label {
  font-size: 11px;
  font-weight: 500;
}
</style>
