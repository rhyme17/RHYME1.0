<template>
  <el-dialog v-model="visible" title="登录" width="400" @close="$emit('close')">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="登录" name="login">
        <el-form :model="loginForm" @submit.prevent="handleLogin" label-position="top">
          <el-form-item label="用户名">
            <el-input v-model="loginForm.username" placeholder="输入用户名" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="loginForm.password" type="password" placeholder="输入密码" show-password />
          </el-form-item>
          <el-button type="primary" style="width:100%" @click="handleLogin" :loading="loading">登录</el-button>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="注册" name="register">
        <el-form :model="registerForm" @submit.prevent="handleRegister" label-position="top">
          <el-form-item label="用户名">
            <el-input v-model="registerForm.username" placeholder="2-50个字符" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="registerForm.password" type="password" placeholder="至少6位" show-password />
          </el-form-item>
          <el-form-item label="邮箱（可选）">
            <el-input v-model="registerForm.email" placeholder="your@email.com" />
          </el-form-item>
          <el-button type="primary" style="width:100%" @click="handleRegister" :loading="loading">注册</el-button>
        </el-form>
      </el-tab-pane>
    </el-tabs>
    <div class="divider">
      <span>或</span>
    </div>
    <el-button style="width:100%" @click="handleGitHubLogin">
      <svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor" style="margin-right:6px;vertical-align:-2px"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
      GitHub 登录
    </el-button>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const props = defineProps({ modelValue: Boolean })
const emit = defineEmits(['update:modelValue', 'close'])

const authStore = useAuthStore()
const visible = ref(props.modelValue)
const activeTab = ref('login')
const loading = ref(false)

const loginForm = ref({ username: '', password: '' })
const registerForm = ref({ username: '', password: '', email: '' })

async function handleLogin() {
  if (!loginForm.value.username || !loginForm.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await authStore.loginWithPassword(loginForm.value.username, loginForm.value.password)
    ElMessage.success('登录成功')
    visible.value = false
    emit('close')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (!registerForm.value.username || !registerForm.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  if (registerForm.value.password.length < 6) {
    ElMessage.warning('密码至少6位')
    return
  }
  loading.value = true
  try {
    await authStore.register(registerForm.value.username, registerForm.value.password, registerForm.value.email || undefined)
    ElMessage.success('注册成功')
    visible.value = false
    emit('close')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}

async function handleGitHubLogin() {
  try {
    await authStore.loginWithGitHub()
  } catch (e) {
    ElMessage.error('GitHub 登录失败')
  }
}
</script>

<style scoped>
.divider {
  display: flex;
  align-items: center;
  margin: 16px 0;
  color: var(--text-muted);
  font-size: 13px;
}
.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
}
.divider span {
  padding: 0 12px;
}
</style>
