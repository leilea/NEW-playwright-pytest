<script setup lang="ts">
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import * as api from '@/api/suites'
import * as casesApi from '@/api/cases'

const router = useRouter()
const qc = useQueryClient()
const { data, isLoading } = useQuery({ queryKey: ['suites'], queryFn: api.list })

const dialogVisible = ref(false)
const formRef = ref<FormInstance>()
const form = reactive({ name: '', version: '', description: '' })
const rules: FormRules = {
  name: [{ required: true, message: '请输入系统名称', trigger: 'blur' }],
}

const editDialogVisible = ref(false)
const editFormRef = ref<FormInstance>()
const editForm = reactive({ id: 0, name: '', version: '', description: '' })
const editingId = ref(0)

function openDialog() {
  form.name = ''
  form.version = ''
  form.description = ''
  dialogVisible.value = true
}

function openEditDialog(row: { id: number; name: string; version: string; description: string }) {
  editingId.value = row.id
  editForm.id = row.id
  editForm.name = row.name
  editForm.version = row.version
  editForm.description = row.description
  editDialogVisible.value = true
}

const create = useMutation({
  mutationFn: (data: { name: string; version?: string; description?: string }) => {
    if (!data.name.trim()) throw new Error('请输入系统名称')
    return api.create(data)
  },
  onSuccess: () => {
    ElMessage.success('已创建')
    dialogVisible.value = false
    location.reload()
  },
  onError: (e: any) => { ElMessage.warning(e?.message || '创建失败') },
})

const updateMutation = useMutation({
  mutationFn: (data: { id: number; name: string; version?: string; description?: string }) => {
    if (!data.name.trim()) throw new Error('请输入系统名称')
    return api.update(data.id, { name: data.name, version: data.version, description: data.description })
  },
  onSuccess: () => {
    ElMessage.success('已修改')
    editDialogVisible.value = false
    location.reload()
  },
  onError: (e: any) => { ElMessage.warning(e?.message || '修改失败') },
})

async function onSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  create.mutate({ ...form })
}

async function onEditSubmit() {
  const valid = await editFormRef.value?.validate().catch(() => false)
  if (!valid) return
  updateMutation.mutate({ ...editForm })
}

const remove = useMutation({
  mutationFn: api.remove,
  onSuccess: () => qc.invalidateQueries({ queryKey: ['suites'] }),
})
async function onDelete(id: number) {
  try {
    const cases = await casesApi.list(id)
    if (cases.length > 0) {
      ElMessage.warning('该系统中存在测试用例，无法删除')
      return
    }
    ElMessageBox.confirm('确认删除该系统？删除后不可恢复。').then(() => remove.mutate(id)).catch(() => {})
  } catch {
    ElMessage.error('无法检查系统用例，请稍后重试')
  }
}
</script>

<template>
  <div class="suites-page">
    <div class="page-header">
      <h2>用例仓库</h2>
      <el-button type="primary" @click="openDialog">新增</el-button>
    </div>

    <el-table :data="data || []" v-loading="isLoading" stripe border style="width:100%">
      <el-table-column type="index" label="序号" width="60" align="center" />
      <el-table-column prop="name" label="系统名称" min-width="180" show-overflow-tooltip align="center" />
      <el-table-column prop="version" label="版本号" min-width="100" align="center" />
      <el-table-column prop="description" label="描述" min-width="120" show-overflow-tooltip align="center" />
      <el-table-column prop="case_count" label="用例数量" width="100" align="center" />
      <el-table-column label="系统创建日期" min-width="160" align="center">
        <template #default="{ row }">
          {{ row.created_at ? new Date(row.created_at).toLocaleString('zh-CN') : '' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280" align="center">
        <template #default="{ row }">
          <el-button size="small" @click="router.push(`/suites/${row.id}`)">详情</el-button>
          <el-button size="small" type="primary" class="action-btn" @click="openEditDialog(row)">修改</el-button>
          <el-button size="small" type="danger" class="action-btn" @click="onDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="新增系统" width="480px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" @submit.prevent="onSubmit">
        <el-form-item label="系统名称" prop="name">
          <el-input v-model="form.name" maxlength="120" placeholder="输入系统名称" />
        </el-form-item>
        <el-form-item label="版本号">
          <el-input v-model="form.version" maxlength="32" placeholder="如 1.0.0" />
        </el-form-item>
        <el-form-item label="系统描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="简要描述该系统" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="create.isPending.value" @click="onSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editDialogVisible" title="修改系统" width="480px" :close-on-click-modal="false">
      <el-form ref="editFormRef" :model="editForm" :rules="rules" label-width="80px" @submit.prevent="onEditSubmit">
        <el-form-item label="系统名称" prop="name">
          <el-input v-model="editForm.name" maxlength="120" placeholder="输入系统名称" />
        </el-form-item>
        <el-form-item label="版本号">
          <el-input v-model="editForm.version" maxlength="32" placeholder="如 1.0.0" />
        </el-form-item>
        <el-form-item label="系统描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="简要描述该系统" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="updateMutation.isPending.value" @click="onEditSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.suites-page {
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
}

.action-btn {
  margin-left: 8px;
}

.suites-page :deep(.el-table) {
  font-size: 16px;
}
</style>
