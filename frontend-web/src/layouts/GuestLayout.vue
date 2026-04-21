<template>
  <div class="guest-layout">
    <header class="guest-header">
      <div class="header-inner">
        <router-link to="/" class="logo">
          <span class="logo-icon">♪</span>
          <span class="logo-text">RHYME</span>
        </router-link>
        <nav class="nav-links">
          <router-link to="/">发现</router-link>
          <router-link to="/search">搜索</router-link>
          <template v-if="authStore.isLoggedIn && authStore.isAdmin">
            <router-link to="/admin" class="admin-link">管理后台</router-link>
          </template>
        </nav>
        <div class="header-actions">
          <template v-if="authStore.isLoggedIn">
            <el-dropdown>
              <span class="user-badge">
                <el-avatar :size="28" :src="authStore.user?.github_avatar" />
                <span class="user-name">{{ authStore.user?.username }}</span>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="authStore.logout()">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <el-button type="primary" size="small" @click="showLogin = true">登录</el-button>
          </template>
        </div>
      </div>
    </header>
    <main class="guest-main">
      <router-view />
    </main>
    <PlayerBar />
    <LoginDialog v-model="showLogin" @close="showLogin = false" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import PlayerBar from '../components/PlayerBar.vue'
import LoginDialog from '../components/LoginDialog.vue'

const authStore = useAuthStore()
const showLogin = ref(false)
</script>

<style scoped>
.guest-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.guest-header {
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(10, 10, 15, 0.85);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
}
.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  height: 60px;
  display: flex;
  align-items: center;
  gap: 32px;
}
.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 20px;
  color: var(--text-primary);
  text-decoration: none;
}
.logo-icon {
  font-size: 24px;
  color: var(--accent);
}
.nav-links {
  display: flex;
  gap: 24px;
  flex: 1;
}
.nav-links a {
  color: var(--text-secondary);
  font-size: 14px;
  transition: color 0.2s;
}
.nav-links a:hover,
.nav-links a.router-link-active {
  color: var(--accent);
}
.admin-link {
  color: var(--accent) !important;
  font-weight: 600;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.user-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--text-primary);
}
.user-name {
  font-size: 14px;
}
.guest-main {
  flex: 1;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 32px 24px 100px;
}
</style>
