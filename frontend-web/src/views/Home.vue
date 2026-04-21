<template>
  <div class="home-page">
    <section class="hero">
      <h1>发现音乐</h1>
      <p>浏览和管理你的个人音乐库</p>
    </section>
    <section class="music-grid">
      <div v-for="music in musics" :key="music.id" class="music-card" @click="play(music)">
        <div class="card-cover">
          <img v-if="music.cover_url" :src="music.cover_url" />
          <div v-else class="cover-fallback">
            <span>♪</span>
          </div>
          <div class="play-overlay">▶</div>
        </div>
        <div class="card-info">
          <div class="card-title">{{ music.title }}</div>
          <div class="card-artist">{{ music.artist }}</div>
          <div class="card-meta">
            <span>{{ formatDuration(music.duration) }}</span>
            <span>{{ music.format.toUpperCase() }}</span>
          </div>
          <div class="card-tags" v-if="music.tags?.length">
            <el-tag v-for="tag in music.tags" :key="tag.id" size="small" :color="tag.color" effect="dark" round>
              {{ tag.name }}
            </el-tag>
          </div>
        </div>
      </div>
    </section>
    <div class="pagination" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="fetchMusics"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import api from '../api'

const player = inject('player')
const musics = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20

async function fetchMusics() {
  const { data } = await api.get('/api/musics/', { params: { page: page.value, page_size: pageSize } })
  musics.value = data.items
  total.value = data.total
}

function play(music) {
  player.playMusic(music)
}

function formatDuration(seconds) {
  if (!seconds) return '--:--'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

onMounted(fetchMusics)
</script>

<style scoped>
.hero {
  text-align: center;
  padding: 48px 0 40px;
}
.hero h1 {
  font-size: 36px;
  font-weight: 800;
  margin-bottom: 8px;
  background: linear-gradient(135deg, var(--accent), #fc5c7c);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.hero p {
  color: var(--text-secondary);
  font-size: 16px;
}
.music-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}
.music-card {
  background: var(--bg-card);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  border: 1px solid var(--border);
}
.music-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(124, 92, 252, 0.15);
}
.card-cover {
  position: relative;
  aspect-ratio: 1;
  background: var(--bg-elevated);
}
.card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.cover-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  color: var(--text-muted);
}
.play-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.4);
  opacity: 0;
  transition: opacity 0.2s;
  font-size: 32px;
  color: white;
}
.music-card:hover .play-overlay {
  opacity: 1;
}
.card-info {
  padding: 12px;
}
.card-title {
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.card-artist {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.card-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 6px;
}
.card-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-top: 6px;
}
.pagination {
  display: flex;
  justify-content: center;
  margin-top: 32px;
}
</style>
