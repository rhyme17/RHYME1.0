<template>
  <div class="admin-layout">
    <aside class="admin-sidebar">
      <div class="sidebar-logo">
        <span class="logo-icon">♪</span>
        <span>RHYME</span>
        <el-tag size="small" type="danger" style="margin-left:8px">Admin</el-tag>
      </div>
      <el-menu :default-active="route.path" router>
        <el-menu-item index="/admin">
          <el-icon><Monitor /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/admin/musics">
          <el-icon><Headset /></el-icon>
          <span>音乐管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/upload">
          <el-icon><Upload /></el-icon>
          <span>上传音乐</span>
        </el-menu-item>
        <el-menu-item index="/admin/tags">
          <el-icon><PriceTag /></el-icon>
          <span>标签管理</span>
        </el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <router-link to="/" class="back-link">← 返回前台</router-link>
      </div>
    </aside>
    <main class="admin-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { Monitor, Headset, Upload, PriceTag } from '@element-plus/icons-vue'

const route = useRoute()
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
}
.admin-sidebar {
  width: 220px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
}
.sidebar-logo {
  padding: 20px;
  font-size: 18px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid var(--border);
}
.logo-icon {
  color: var(--accent);
  font-size: 22px;
}
.sidebar-footer {
  margin-top: auto;
  padding: 16px 20px;
  border-top: 1px solid var(--border);
}
.back-link {
  font-size: 13px;
  color: var(--text-muted);
}
.admin-main {
  flex: 1;
  margin-left: 220px;
  padding: 32px;
}
</style>
