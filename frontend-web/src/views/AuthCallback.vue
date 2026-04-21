<template>
  <div class="callback-page">
    <div class="callback-card">
      <div class="spinner"></div>
      <p>正在完成 GitHub 认证...</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

onMounted(() => {
  const token = route.query.token
  const isAdmin = route.query.is_admin
  if (token) {
    authStore.handleCallback(token, isAdmin)
    if (isAdmin === '1') {
      router.push('/admin')
    } else {
      router.push('/')
    }
  } else {
    router.push('/')
  }
})
</script>

<style scoped>
.callback-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
}
.callback-card {
  text-align: center;
  color: var(--text-secondary);
}
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
