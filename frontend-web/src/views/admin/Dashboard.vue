<template>
  <div class="dashboard">
    <h2>仪表盘</h2>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ stats.musicCount }}</div>
        <div class="stat-label">音乐总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.tagCount }}</div>
        <div class="stat-label">标签总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ formatSize(stats.totalSize) }}</div>
        <div class="stat-label">存储占用</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'

const stats = ref({ musicCount: 0, tagCount: 0, totalSize: 0 })

async function fetchStats() {
  const [musicsRes, tagsRes] = await Promise.all([
    api.get('/api/musics/', { params: { page_size: 1 } }),
    api.get('/api/tags/'),
  ])
  stats.value.musicCount = musicsRes.data.total
  stats.value.tagCount = tagsRes.data.length
  let totalSize = 0
  if (musicsRes.data.total > 0) {
    const allRes = await api.get('/api/musics/', { params: { page_size: 100 } })
    totalSize = allRes.data.items.reduce((sum, m) => sum + (m.file_size || 0), 0)
  }
  stats.value.totalSize = totalSize
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${size.toFixed(1)} ${units[i]}`
}

onMounted(fetchStats)
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-top: 24px;
}
.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  text-align: center;
}
.stat-value {
  font-size: 32px;
  font-weight: 800;
  color: var(--accent);
}
.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 4px;
}
</style>
