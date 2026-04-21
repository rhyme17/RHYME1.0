<template>
  <div class="admin-musics">
    <div class="page-header">
      <h2>音乐管理</h2>
      <router-link to="/admin/upload">
        <el-button type="primary">上传音乐</el-button>
      </router-link>
    </div>
    <el-table :data="musics" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="封面" width="60">
        <template #default="{ row }">
          <el-avatar :size="32" :src="row.cover_url || ''" shape="square">
            ♪
          </el-avatar>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip />
      <el-table-column prop="artist" label="艺术家" min-width="120" show-overflow-tooltip />
      <el-table-column prop="album" label="专辑" min-width="120" show-overflow-tooltip />
      <el-table-column label="时长" width="80">
        <template #default="{ row }">{{ formatDuration(row.duration) }}</template>
      </el-table-column>
      <el-table-column prop="format" label="格式" width="70" />
      <el-table-column label="标签" min-width="120">
        <template #default="{ row }">
          <el-tag v-for="tag in row.tags" :key="tag.id" size="small" round style="margin:2px">{{ tag.name }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="editMusic(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="deleteMusic(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="pagination">
      <el-pagination v-model:current-page="page" :page-size="20" :total="total" layout="prev, pager, next" @current-change="fetchMusics" />
    </div>

    <el-dialog v-model="editDialogVisible" title="编辑音乐" width="500">
      <el-form :model="editForm" label-width="60px">
        <el-form-item label="标题"><el-input v-model="editForm.title" /></el-form-item>
        <el-form-item label="艺术家"><el-input v-model="editForm.artist" /></el-form-item>
        <el-form-item label="专辑"><el-input v-model="editForm.album" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const musics = ref([])
const total = ref(0)
const page = ref(1)
const editDialogVisible = ref(false)
const editForm = ref({ id: 0, title: '', artist: '', album: '' })

async function fetchMusics() {
  const { data } = await api.get('/api/musics/', { params: { page: page.value, page_size: 20 } })
  musics.value = data.items
  total.value = data.total
}

function editMusic(music) {
  editForm.value = { id: music.id, title: music.title, artist: music.artist, album: music.album }
  editDialogVisible.value = true
}

async function saveEdit() {
  await api.put(`/api/musics/${editForm.value.id}`, {
    title: editForm.value.title,
    artist: editForm.value.artist,
    album: editForm.value.album,
  })
  editDialogVisible.value = false
  ElMessage.success('保存成功')
  fetchMusics()
}

async function deleteMusic(music) {
  await ElMessageBox.confirm(`确定删除「${music.title}」？`, '确认删除', { type: 'warning' })
  await api.delete(`/api/musics/${music.id}`)
  ElMessage.success('已删除')
  fetchMusics()
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
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
