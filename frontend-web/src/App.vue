<template>
  <router-view />
  <audio ref="audioRef" @timeupdate="onTimeUpdate" @ended="onEnded" @loadedmetadata="onLoaded" />
</template>

<script setup>
import { ref, provide } from 'vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
if (authStore.isLoggedIn) {
  authStore.fetchUser()
}

const audioRef = ref(null)
const currentMusic = ref(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)

function playMusic(music) {
  if (!music?.stream_url) return
  currentMusic.value = music
  audioRef.value.src = music.stream_url
  audioRef.value.play()
  isPlaying.value = true
}

function togglePlay() {
  if (!audioRef.value) return
  if (isPlaying.value) {
    audioRef.value.pause()
  } else {
    audioRef.value.play()
  }
  isPlaying.value = !isPlaying.value
}

function seek(time) {
  if (audioRef.value) {
    audioRef.value.currentTime = time
  }
}

function onTimeUpdate() {
  currentTime.value = audioRef.value?.currentTime || 0
}

function onEnded() {
  isPlaying.value = false
  currentTime.value = 0
}

function onLoaded() {
  duration.value = audioRef.value?.duration || 0
}

provide('player', {
  currentMusic,
  isPlaying,
  currentTime,
  duration,
  playMusic,
  togglePlay,
  seek,
})
</script>
