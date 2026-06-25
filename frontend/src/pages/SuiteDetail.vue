<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as suitesApi from '@/api/suites'
import * as casesApi from '@/api/cases'
import RecorderPanel from '@/components/RecorderPanel.vue'
import type { Step } from '@/types/step'

const route = useRoute()
const router = useRouter()
const qc = useQueryClient()

const suiteId = computed(() => Number(route.params.id))
const showRecorder = ref(false)

const { data: suite } = useQuery({
  queryKey: ['suite', suiteId.value],
  queryFn: () => suitesApi.get(suiteId.value),
})

const { data: cases, isLoading: casesLoading } = useQuery({
  queryKey: ['cases', suiteId.value],
  queryFn: () => casesApi.list(suiteId.value),
})

const createCaseMutation = useMutation({
  mutationFn: (payload: { name: string; steps: Step[] }) =>
    casesApi.create({ suite_id: suiteId.value, name: payload.name, steps: payload.steps }),
  onSuccess: () => {
    ElMessage.success('用例已创建')
    showRecorder.value = false
    location.reload()
  },
  onError: (err: unknown) => {
    ElMessage.error(`创建失败: ${err}`)
  },
})

const deleteMutation = useMutation({
  mutationFn: casesApi.remove,
  onSuccess: () => {
    ElMessage.success('已删除')
    location.reload()
  },
})

function onCreateCase(payload: { name: string; steps: Step[]; url: string }) {
  createCaseMutation.mutate({ name: payload.name, steps: payload.steps })
}

function onDelete(id: number) {
  ElMessageBox.confirm('确认删除该用例？').then(() => deleteMutation.mutate(id)).catch(() => {})
}

function stepCount(steps: Step[]): number {
  return Array.isArray(steps) ? steps.length : 0
}

function dateStr(ts: string): string {
  return ts?.slice(0, 10) || ''
}
</script>

<template>
  <div v-if="suite">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
      <div>
        <h2 style="margin:0">系统: {{ suite.name }}</h2>
        <p style="color:var(--el-text-color-secondary);margin:4px 0 0">{{ suite.description || '暂无描述' }}</p>
      </div>
    </div>

    <div style="margin-bottom:16px;display:flex;justify-content:flex-end;align-items:center;gap:8px">
      <el-button @click="router.push('/suites')">返回</el-button>
      <el-button @click="router.push(`/cases/new?suite_id=${suiteId}`)">手动新建</el-button>
      <el-button type="primary" @click="showRecorder = true">录制新用例</el-button>
    </div>

    <el-dialog v-model="showRecorder" title="录制新用例" width="800px"
               :close-on-click-modal="false" destroy-on-close>
      <RecorderPanel @create-case="onCreateCase" />
    </el-dialog>

    <el-table :data="cases || []" v-loading="casesLoading" stripe empty-text="暂无用例，点击上方按钮创建" style="width:100%;font-size:16px">
      <el-table-column type="index" label="序号" width="60" align="center" />
      <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip align="center">
        <template #default="{ row }">
          <router-link :to="`/cases/${row.id}`" style="font-weight:500">{{ row.name }}</router-link>
        </template>
      </el-table-column>
      <el-table-column label="标签" min-width="140" align="center">
        <template #default="{ row }">
          <el-tag v-for="t in row.tags" :key="t" size="small" style="margin-right:4px">{{ t }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="步骤数" width="80" align="center">
        <template #default="{ row }">
          {{ stepCount(row.steps) }}
        </template>
      </el-table-column>
      <el-table-column label="创建时间" min-width="100" align="center">
        <template #default="{ row }">
          {{ dateStr(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" align="center">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="router.push(`/cases/${row.id}`)">编辑</el-button>
          <el-button size="small" type="danger" style="margin-left:4px" @click="onDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
  <el-skeleton v-else :rows="4" animated />
</template>
