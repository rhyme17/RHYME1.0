<template>
  <div class="player-bar" v-if="player.currentMusic.value">
    <div class="player-cover">
      <img v-if="player.currentMusic.value?.cover_url" :src="player.currentMusic.value.cover_url" />
      <div v-else class="cover-placeholder">♪</div>
    </div>
    <div class="player-info">
      <div class="player-title">{{ player.currentMusic.value?.title }}</div>
      <div class="player-artist">{{ player.currentMusic.value?.artist }}</div>
    </div>
    <div class="player-controls">
      <button class="ctrl-btn" @click="player.togglePlay()">
        {{ player.isPlaying.value ? '⏸' : '▶' }}
      </button>
    </div>
    <div class="player-progress">
      <span class="time">{{ formatTime(player.currentTime.value) }}</span>
      <input
        type="range"
        :min="0"
        :max="player.duration.value || 0"
        :value="player.currentTime.value"
        @input="player.seek(Number($event.target.value))"
        class="progress-slider"
      />
      <span class="time">{{ formatTime(player.duration.value) }}</span>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue'

const player = inject('player')

function formatTime(seconds) {
  if (!seconds || !isFinite(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.player-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 72px;
  background: rgba(18, 18, 26, 0.95);
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 24px;
  z-index: 100;
  backdrop-filter: blur(20px);
  gap: 16px;
}
.player-cover {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}
.player-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-elevated);
  color: var(--accent);
  font-size: 20px;
}
.player-info {
  min-width: 120px;
  max-width: 200px;
}
.player-title {
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.player-artist {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.player-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}
.ctrl-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: var(--accent);
  color: white;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}
.ctrl-btn:hover {
  background: var(--accent-hover);
}
.player-progress {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}
.time {
  font-size: 12px;
  color: var(--text-muted);
  min-width: 36px;
  text-align: center;
}
.progress-slider {
  flex: 1;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--border);
  border-radius: 2px;
  outline: none;
  cursor: pointer;
}
.progress-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
}
</style>
