<template>
  <div class="search-page">
    <h2>搜索音乐</h2>
    <div class="search-bar">
      <el-input
        v-model="query"
        placeholder="搜索歌曲、艺术家、专辑..."
        size="large"
        clearable
        @keyup.enter="doSearch"
        @clear="doSearch"
      >
        <template #append>
          <el-button @click="doSearch" :loading="searching">搜索</el-button>
        </template>
      </el-input>
    </div>

    <div v-if="searched" class="search-results">
      <section v-if="libraryResults.length" class="result-section">
        <h3 class="section-title">
          <span class="section-icon">📚</span> 音乐库 ({{ libraryResults.length }})
        </h3>
        <div v-for="item in libraryResults" :key="'lib-' + item.id" class="result-row" @click="playLibrary(item)">
          <div class="result-cover">
            <img v-if="item.cover_url" :src="item.cover_url" />
            <div v-else class="cover-fallback">♪</div>
          </div>
          <div class="result-info">
            <div class="result-title">{{ item.name }}</div>
            <div class="result-artist">{{ item.artist }} · {{ item.album }}</div>
          </div>
          <div class="result-duration">{{ formatDuration(item.duration) }}</div>
          <el-tag size="small" type="success" effect="dark" round>音乐库</el-tag>
        </div>
      </section>

      <section v-if="onlineResults.length" class="result-section">
        <h3 class="section-title">
          <span class="section-icon">🌐</span> 在线搜索 ({{ onlineResults.length }})
        </h3>
        <div v-for="item in onlineResults" :key="'on-' + item.id" class="result-row online-row">
          <div class="result-cover">
            <div class="cover-fallback online-cover">♫</div>
          </div>
          <div class="result-info">
            <div class="result-title">{{ item.name }}</div>
            <div class="result-artist">{{ item.artist }} · {{ item.album }}</div>
          </div>
          <div class="result-actions">
            <el-button size="small" @click="importSong(item)" :loading="importingId === item.id" type="primary" plain>
              导入音乐库
            </el-button>
          </div>
          <el-tag size="small" effect="dark" round>在线</el-tag>
        </div>
      </section>

      <div v-if="!libraryResults.length && !onlineResults.length" class="empty">
        <p>没有找到相关音乐</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { inject } from 'vue'
import api from '../api'

const player = inject('player')
const query = ref('')
const searching = ref(false)
const searched = ref(false)
const libraryResults = ref([])
const onlineResults = ref([])
const importingId = ref('')

async function doSearch() {
  if (!query.value.trim()) {
    libraryResults.value = []
    onlineResults.value = []
    searched.value = false
    return
  }
  searching.value = true
  try {
    const { data } = await api.get('/api/online/unified-search', { params: { keyword: query.value } })
    libraryResults.value = data.library || []
    onlineResults.value = data.online || []
    searched.value = true
  } catch (e) {
    ElMessage.error('搜索失败')
  } finally {
    searching.value = false
  }
}

function playLibrary(item) {
  player.playMusic(item)
}

async function importSong(item) {
  importingId.value = item.id
  try {
    const { data } = await api.post('/api/online/import', null, {
      params: {
        id: item.id,
        source: 'netease',
        name: item.name,
        artist: item.artist,
        album: item.album,
      },
    })
    ElMessage.success(`已导入: ${data.music.title}`)
    libraryResults.value.unshift({
      source: 'library',
      id: String(data.music.id),
      name: data.music.title,
      artist: data.music.artist,
      album: data.music.album,
      duration: data.music.duration,
      stream_url: data.music.stream_url,
      cover_url: data.music.cover_url,
    })
    onlineResults.value = onlineResults.value.filter(r => r.id !== item.id)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '导入失败')
  } finally {
    importingId.value = ''
  }
}

function formatDuration(seconds) {
  if (!seconds) return '--:--'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.search-page {
  max-width: 900px;
  margin: 0 auto;
}
h2 {
  font-size: 24px;
  margin-bottom: 20px;
}
.search-bar {
  margin-bottom: 24px;
}
.result-section {
  margin-bottom: 32px;
}
.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.section-icon {
  font-size: 18px;
}
.result-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}
.result-row:hover {
  background: var(--accent-dim);
}
.online-row {
  cursor: default;
}
.result-cover {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
}
.result-cover img {
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
  background: var(--bg-elevated);
  color: var(--text-muted);
  font-size: 20px;
}
.online-cover {
  background: rgba(124, 92, 252, 0.15);
  color: var(--accent);
}
.result-info {
  flex: 1;
  min-width: 0;
}
.result-title {
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.result-artist {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.result-duration {
  font-size: 13px;
  color: var(--text-muted);
}
.result-actions {
  flex-shrink: 0;
}
.empty {
  text-align: center;
  color: var(--text-muted);
  padding: 48px 0;
}
</style>
