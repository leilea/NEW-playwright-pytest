import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api/auth'
import type { User } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const roles = computed(() => user.value?.roles ?? [])

  async function refresh() {
    try { user.value = await api.fetchMe() }
    catch { user.value = null }
  }
  async function login(email: string, password: string) {
    await api.login(email, password)
    await refresh()
  }
  async function logout() {
    await api.logout()
    user.value = null
    token.value = null
    location.href = '/login'
  }
  function hasRole(r: string) { return roles.value.includes(r as any) }
  function clearAuth() { user.value = null; token.value = null }
  return { user, token, roles, refresh, login, logout, hasRole, clearAuth }
})
