import { createRouter, createWebHistory } from 'vue-router'
import Profile from '@/views/Profile.vue'
import Matches from '@/views/Matches.vue'
import MatchDetail from '@/views/MatchDetail.vue'
import CreateMatch from '@/views/CreateMatch.vue'
import Friends from '@/views/Friends.vue'
import SubmitStats from '@/views/SubmitStats.vue'

const routes = [
  { path: '/', redirect: '/matches' },
  { path: '/profile', name: 'Profile', component: Profile },
  { path: '/matches', name: 'Matches', component: Matches },
  { path: '/matches/create', name: 'CreateMatch', component: CreateMatch },
  { path: '/matches/:id', name: 'MatchDetail', component: MatchDetail },
  { path: '/matches/:id/stats', name: 'SubmitStats', component: SubmitStats },
  { path: '/friends', name: 'Friends', component: Friends },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
