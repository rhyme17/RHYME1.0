<template>
  <div class="tags-page">
    <div class="page-header">
      <h2>标签管理</h2>
      <el-button type="primary" @click="showCreateDialog">新建标签</el-button>
    </div>
    <el-table :data="tags" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="名称" />
      <el-table-column label="颜色" width="100">
        <template #default="{ row }">
          <span class="color-dot" :style="{ background: row.color }"></span>
          {{ row.color }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="editTag(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="deleteTag(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑标签' : '新建标签'" width="400">
      <el-form :model="form" label-width="60px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="form.color" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTag">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const tags = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const form = ref({ id: 0, name: '', color: '#7c5cfc' })

async function fetchTags() {
  const { data } = await api.get('/api/tags/')
  tags.value = data
}

function showCreateDialog() {
  isEdit.value = false
  form.value = { id: 0, name: '', color: '#7c5cfc' }
  dialogVisible.value = true
}

function editTag(tag) {
  isEdit.value = true
  form.value = { id: tag.id, name: tag.name, color: tag.color || '#7c5cfc' }
  dialogVisible.value = true
}

async function saveTag() {
  if (isEdit.value) {
    await api.put(`/api/tags/${form.value.id}`, { name: form.value.name, color: form.value.color })
  } else {
    await api.post('/api/tags/', { name: form.value.name, color: form.value.color })
  }
  dialogVisible.value = false
  ElMessage.success('保存成功')
  fetchTags()
}

async function deleteTag(tag) {
  await ElMessageBox.confirm(`确定删除标签「${tag.name}」？`, '确认删除', { type: 'warning' })
  await api.delete(`/api/tags/${tag.id}`)
  ElMessage.success('已删除')
  fetchTags()
}

onMounted(fetchTags)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.color-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  vertical-align: middle;
  margin-right: 6px;
}
</style>
