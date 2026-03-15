import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_URL,
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const tg = window.Telegram?.WebApp
  const hasInitData = tg?.initData && tg.initData.length > 0

  if (hasInitData) {
    config.headers['X-Init-Data'] = tg.initData
  } else {
    // Dev mode: use bot auth header with test telegram_id
    config.headers['X-Bot-Auth'] = '999999999'
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'Ошибка сети'
    return Promise.reject(new Error(msg))
  }
)

export default api

export const authApi = {
  telegram: () => api.post('/auth/telegram'),
  botRegister: (data) => api.post('/auth/bot-register', data),
}

export const usersApi = {
  me: () => api.get('/users/me'),
  updateMe: (data) => api.patch('/users/me', data),
  getUser: (id) => api.get(`/users/${id}`),
  search: (q) => api.get('/users/search', { params: { q } }),
  sendFriendRequest: (receiverTgId) =>
    api.post('/users/friends/request', { receiver_telegram_id: receiverTgId }),
  getFriendRequests: () => api.get('/users/friends/requests'),
  getFriends: () => api.get('/users/friends/list'),
  acceptFriendRequest: (id) => api.post(`/users/friends/requests/${id}/accept`),
  declineFriendRequest: (id) => api.post(`/users/friends/requests/${id}/decline`),
}

export const matchesApi = {
  list: (params) => api.get('/matches', { params }),
  search: (q) => api.get('/matches/search', { params: { q } }),
  get: (id) => api.get(`/matches/${id}`),
  create: (data) => api.post('/matches', data),
  update: (id, data) => api.patch(`/matches/${id}`, data),
  join: (id, asReferee = false) =>
    api.post(`/matches/${id}/join`, null, { params: { as_referee: asReferee } }),
  leave: (id) => api.post(`/matches/${id}/leave`),
  invite: (matchId, userId) => api.post(`/matches/${matchId}/invite/${userId}`),
  acceptInvite: (id) => api.post(`/matches/${id}/accept-invite`),
  uploadReceipt: (id, file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/matches/${id}/upload-receipt`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  getReceipts: (id) => api.get(`/matches/${id}/receipts`),
  reviewReceipt: (matchId, receiptId, data) =>
    api.patch(`/matches/${matchId}/receipts/${receiptId}`, data),
  submitStats: (id, data) => api.post(`/matches/${id}/stats`, data),
  getStats: (id) => api.get(`/matches/${id}/stats`),
}
