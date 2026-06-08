<script setup lang="ts">
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as api from '@/api/suites'

const qc = useQueryClient()
const { data, isLoading } = useQuery({ queryKey: ['suites'], queryFn: api.list })

const form = ref({ name: '', description: '' })
const create = useMutation({
  mutationFn: api.create,
  onSuccess: () => { qc.invalidateQueries({ queryKey: ['suites'] }); ElMessage.success('已创建'); form.value = { name: '', description: '' } },
})
const remove = useMutation({
  mutationFn: api.remove,
  onSuccess: () => qc.invalidateQueries({ queryKey: ['suites'] }),
})
function onDelete(id: number) {
  ElMessageBox.confirm('确认删除?').then(() => remove.mutate(id)).catch(() => {})
}
</script>

<template>
  <h2>测试套件</h2>
  <el-form inline @submit.prevent="create.mutate(form)">
    <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
    <el-form-item label="描述"><el-input v-model="form.description" /></el-form-item>
    <el-button type="primary" native-type="submit" :loading="create.isPending.value">新建</el-button>
  </el-form>
  <el-table :data="data || []" v-loading="isLoading" stripe>
    <el-table-column prop="id" label="ID" width="60" />
    <el-table-column prop="name" label="名称" />
    <el-table-column prop="description" label="描述" />
    <el-table-column label="操作" width="160">
      <template #default="{ row }">
        <router-link :to="`/suites/${row.id}`">详情</router-link>
        <el-button size="small" type="danger" style="margin-left:8px" @click="onDelete(row.id)">删除</el-button>
      </template>
    </el-table-column>
  </el-table>
</template>
