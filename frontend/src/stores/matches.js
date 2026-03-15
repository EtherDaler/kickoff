import { defineStore } from 'pinia'
import { ref } from 'vue'
import { matchesApi } from '@/api'

export const useMatchesStore = defineStore('matches', () => {
  const matches = ref([])
  const myMatches = ref([])
  const currentMatch = ref(null)
  const loading = ref(false)

  async function fetchMatches(params = {}) {
    loading.value = true
    try {
      const res = await matchesApi.list(params)
      matches.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchMyMatches() {
    loading.value = true
    try {
      const res = await matchesApi.list({ mine: true })
      myMatches.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchMatch(id) {
    loading.value = true
    try {
      const res = await matchesApi.get(id)
      currentMatch.value = res.data
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function createMatch(data) {
    const res = await matchesApi.create(data)
    return res.data
  }

  async function joinMatch(id, asReferee = false) {
    const res = await matchesApi.join(id, asReferee)
    currentMatch.value = res.data
    return res.data
  }

  async function leaveMatch(id) {
    const res = await matchesApi.leave(id)
    currentMatch.value = res.data
    return res.data
  }

  return {
    matches, myMatches, currentMatch, loading,
    fetchMatches, fetchMyMatches, fetchMatch, createMatch, joinMatch, leaveMatch,
  }
})
