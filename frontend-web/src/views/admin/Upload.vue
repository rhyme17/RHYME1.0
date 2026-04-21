<template>
  <div class="upload-page">
    <h2>上传音乐</h2>
    <el-upload
      class="upload-area"
      drag
      multiple
      :action="'/api/musics/'"
      :headers="uploadHeaders"
      name="file"
      :accept="acceptTypes"
      :on-success="onSuccess"
      :on-error="onError"
    >
      <div class="upload-content">
        <div class="upload-icon">↑</div>
        <div>拖拽文件到此处，或点击上传</div>
        <div class="upload-hint">支持 MP3、FLAC、WAV、OGG、AAC、M4A，单文件最大 50MB</div>
      </div>
    </el-upload>
    <div class="upload-results" v-if="results.length">
      <h3>上传结果</h3>
      <div v-for="(r, i) in results" :key="i" class="result-item" :class="{ success: r.ok, error: !r.ok }">
        {{ r.ok ? `✓ ${r.name} 上传成功` : `✗ ${r.name}: ${r.error}` }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const token = localStorage.getItem('token')
const uploadHeaders = { Authorization: `Bearer ${token}` }
const acceptTypes = '.mp3,.flac,.wav,.ogg,.aac,.m4a'
const results = ref([])

function onSuccess(response) {
  results.value.push({ ok: true, name: response.title })
  ElMessage.success(`${response.title} 上传成功`)
}

function onError(error) {
  let msg = '上传失败'
  try {
    msg = JSON.parse(error.message).detail || msg
  } catch {}
  results.value.push({ ok: false, name: '文件', error: msg })
  ElMessage.error(msg)
}
</script>

<style scoped>
.upload-area {
  margin-top: 20px;
}
.upload-content {
  padding: 40px;
  text-align: center;
  color: var(--text-secondary);
}
.upload-icon {
  font-size: 48px;
  color: var(--accent);
  margin-bottom: 12px;
}
.upload-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 8px;
}
.upload-results {
  margin-top: 24px;
}
.result-item {
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 4px;
  font-size: 13px;
}
.result-item.success {
  background: rgba(92, 252, 154, 0.1);
  color: var(--success);
}
.result-item.error {
  background: rgba(252, 92, 124, 0.1);
  color: var(--danger);
}
</style>
