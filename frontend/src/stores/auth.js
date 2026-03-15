import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, usersApi } from '@/api'

const DEV_USER = {
  telegram_id: 999999999,
  username: 'dev_user',
  first_name: 'Dev',
  last_name: 'User',
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const isDevMode = ref(false)

  const isLoggedIn = computed(() => !!user.value)

  async function init() {
    loading.value = true
    error.value = null
    try {
      const tg = window.Telegram?.WebApp
      const hasInitData = tg?.initData && tg.initData.length > 0

      if (hasInitData) {
        tg.ready()
        tg.expand()
        const res = await authApi.telegram()
        user.value = res.data
      } else {
        // Dev mode: running in browser without Telegram
        isDevMode.value = true
        const res = await authApi.botRegister(DEV_USER)
        user.value = res.data
      }
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function refreshMe() {
    try {
      const res = await usersApi.me()
      user.value = res.data
    } catch (e) {
      console.error('Failed to refresh user', e)
    }
  }

  async function updateProfile(data) {
    const res = await usersApi.updateMe(data)
    user.value = res.data
    return res.data
  }

  return { user, loading, error, isDevMode, isLoggedIn, init, refreshMe, updateProfile }
})
