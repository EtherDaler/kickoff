<template>
  <div class="app" :class="{ 'app--loaded': !authStore.loading }">
    <transition name="fade" mode="out-in">
      <div v-if="authStore.loading" class="splash">
        <div class="splash-inner">
          <div class="splash-ball">⚽</div>
          <p class="splash-text">Football App</p>
          <div class="spinner"></div>
        </div>
      </div>

      <div v-else-if="authStore.error" class="splash">
        <div class="splash-inner">
          <div class="splash-ball">❌</div>
          <p class="splash-text">Ошибка авторизации</p>
          <p style="color: var(--text-secondary); font-size: 14px; margin-top: 8px;">
            {{ authStore.error }}
          </p>
          <button class="btn btn-primary" style="margin-top: 20px;" @click="authStore.init()">
            Попробовать снова
          </button>
        </div>
      </div>

      <div v-else class="main-layout">
        <div v-if="authStore.isDevMode" class="dev-banner">
          🛠 Dev Mode — работает без Telegram (user_id: 999999999)
        </div>
        <router-view v-slot="{ Component, route }">
          <transition name="slide-up" mode="out-in">
            <component :is="Component" :key="route.path" />
          </transition>
        </router-view>
        <BottomNav />
      </div>
    </transition>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import BottomNav from '@/components/BottomNav.vue'

const authStore = useAuthStore()

onMounted(() => {
  authStore.init()
})
</script>

<style>
.app {
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  background: var(--bg-primary);
}

.splash {
  height: 100vh;
  height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
}

.splash-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.splash-ball {
  font-size: 64px;
  animation: bounce 1s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-12px); }
}

.splash-text {
  font-size: 24px;
  font-weight: 800;
  background: linear-gradient(135deg, #4ade80, #22d3ee);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.main-layout {
  height: 100vh;
  height: 100dvh;
  display: flex;
  flex-direction: column;
  position: relative;
}

.dev-banner {
  background: rgba(251, 191, 36, 0.15);
  border-bottom: 1px solid rgba(251, 191, 36, 0.4);
  color: #fbbf24;
  font-size: 12px;
  font-weight: 600;
  padding: 6px 16px;
  text-align: center;
  flex-shrink: 0;
  z-index: 50;
}
</style>
