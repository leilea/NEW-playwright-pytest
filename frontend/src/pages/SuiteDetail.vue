<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { ref, computed, reactive } from 'vue'
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
const editDialogVisible = ref(false)
const editForm = reactive({ id: 0, name: '', version: '' })

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

const editMutation = useMutation({
  mutationFn: (payload: { id: number; name: string; version: string }) =>
    casesApi.patch(payload.id, { name: payload.name, version: payload.version }),
  onSuccess: () => {
    ElMessage.success('已修改')
    editDialogVisible.value = false
    location.reload()
  },
  onError: (err: unknown) => {
    ElMessage.error(`修改失败: ${err}`)
  },
})

function onCreateCase(payload: { name: string; steps: Step[]; url: string }) {
  createCaseMutation.mutate({ name: payload.name, steps: payload.steps })
}

function onDelete(id: number) {
  ElMessageBox.confirm('确认删除该用例？').then(() => deleteMutation.mutate(id)).catch(() => {})
}

function openEditDialog(row: { id: number; name: string; version: string }) {
  editForm.id = row.id
  editForm.name = row.name
  editForm.version = row.version || ''
  editDialogVisible.value = true
}

function onEditSubmit() {
  if (!editForm.name.trim()) {
    ElMessage.warning('请输入用例名称')
    return
  }
  editMutation.mutate({ ...editForm })
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
    <div style="margin-bottom:16px">
      <h2 style="margin:0">系统用例</h2>
      <div style="display:flex;align-items:center;gap:8px;margin-top:8px">
        <span style="color:var(--el-text-color-regular);font-size:14px">所属系统：</span>
        <span style="font-weight:500">{{ suite.name }}</span>
      </div>
      <p style="color:var(--el-text-color-secondary);margin:4px 0 0">{{ suite.description || '暂无描述' }}</p>
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

    <el-table :data="cases || []" v-loading="casesLoading" stripe border empty-text="暂无用例，点击上方按钮创建" style="width:100%;font-size:16px">
      <el-table-column type="index" label="序号" width="60" align="center" />
      <el-table-column prop="name" label="用例名称" min-width="140" show-overflow-tooltip header-align="center">
        <template #default="{ row }">
          <router-link :to="`/cases/${row.id}`" style="font-weight:500;display:block;text-align:left">{{ row.name }}</router-link>
        </template>
      </el-table-column>
      <el-table-column prop="version" label="版本" min-width="100" align="center" />
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
      <el-table-column label="操作" width="220" align="center">
        <template #default="{ row }">
          <el-button size="small" @click="openEditDialog(row)">修改</el-button>
          <el-button size="small" type="primary" @click="router.push(`/cases/${row.id}`)">详情</el-button>
          <el-button size="small" type="danger" style="margin-left:4px" @click="onDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="editDialogVisible" title="修改用例" width="420px" :close-on-click-modal="false">
      <el-form label-width="80px">
        <el-form-item label="用例名称">
          <el-input v-model="editForm.name" maxlength="160" placeholder="输入用例名称" />
        </el-form-item>
        <el-form-item label="版本">
          <el-input v-model="editForm.version" maxlength="32" placeholder="如 1.0.0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editMutation.isPending.value" @click="onEditSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
  <el-skeleton v-else :rows="4" animated />
</template>

<style scoped>
</style>
