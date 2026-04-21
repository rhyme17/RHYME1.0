import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const isAdmin = ref(localStorage.getItem('isAdmin') === '1')
  const user = ref(null)

  const isLoggedIn = computed(() => !!token.value)

  async function fetchUser() {
    if (!token.value) return
    try {
      const { data } = await api.get('/api/auth/me')
      user.value = data
      isAdmin.value = data.is_admin
      localStorage.setItem('isAdmin', data.is_admin ? '1' : '0')
    } catch {
      logout()
    }
  }

  async function loginWithGitHub() {
    const { data } = await api.get('/api/auth/github/authorize')
    window.location.href = data.url
  }

  async function loginWithPassword(username, password) {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)

    const { data } = await api.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })

    token.value = data.access_token
    localStorage.setItem('token', data.access_token)
    await fetchUser()
  }

  async function register(username, password, email) {
    await api.post('/api/auth/register', { username, password, email })
    await loginWithPassword(username, password)
  }

  function handleCallback(queryToken, queryIsAdmin) {
    token.value = queryToken
    isAdmin.value = queryIsAdmin === '1'
    localStorage.setItem('token', queryToken)
    localStorage.setItem('isAdmin', queryIsAdmin)
    fetchUser()
  }

  function logout() {
    token.value = ''
    isAdmin.value = false
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('isAdmin')
  }

  return { token, isAdmin, user, isLoggedIn, fetchUser, loginWithGitHub, loginWithPassword, register, handleCallback, logout }
})
