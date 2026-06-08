<script setup lang="ts">
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as api from '@/api/cases'
import { list as listSuites } from '@/api/suites'

const route = useRoute(); const router = useRouter(); const qc = useQueryClient()
const suiteFilter = ref<number | undefined>(Number(route.query.suite) || undefined)
const { data: suites } = useQuery({ queryKey: ['suites'], queryFn: listSuites })
const { data: cases, isLoading } = useQuery({ queryKey: ['cases', suiteFilter], queryFn: () => api.list(suiteFilter.value) })

const form = ref({ suite_id: suiteFilter.value || 0, name: '' })
const create = useMutation({
  mutationFn: () => api.create({ suite_id: form.value.suite_id, name: form.value.name }),
  onSuccess: () => { qc.invalidateQueries({ queryKey: ['cases'] }); ElMessage.success('已创建'); router.push({ path: '/cases', query: { suite: String(form.value.suite_id) } }) },
})
</script>

<template>
  <h2>测试用例</h2>
  <el-form inline>
    <el-form-item label="套件">
      <el-select v-model="suiteFilter" placeholder="全部" clearable>
        <el-option v-for="s in suites || []" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
    </el-form-item>
  </el-form>
  <el-form inline @submit.prevent="create.mutate()">
    <el-form-item label="套件">
      <el-select v-model="form.suite_id"><el-option v-for="s in suites || []" :key="s.id" :label="s.name" :value="s.id" /></el-select>
    </el-form-item>
    <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
    <el-button native-type="submit" type="primary" :loading="create.isPending.value">新建</el-button>
  </el-form>
  <el-table :data="cases || []" v-loading="isLoading" stripe>
    <el-table-column prop="id" label="ID" width="60" />
    <el-table-column prop="name" label="名称" />
    <el-table-column prop="tags" label="标签">
      <template #default="{ row }">{{ row.tags?.join(', ') }}</template>
    </el-table-column>
    <el-table-column label="操作" width="120">
      <template #default="{ row }">
        <router-link :to="`/cases/${row.id}`">编辑</router-link>
      </template>
    </el-table-column>
  </el-table>
</template>
