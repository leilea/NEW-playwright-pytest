<template>
  <div class="case-editor">
    <h2>{{ isNew ? 'New Case' : 'Edit Case' }}</h2>
    <el-form :model="form" label-width="80px">
      <el-form-item label="Name">
        <el-input v-model="form.name" placeholder="Case name" />
      </el-form-item>
      <el-form-item label="Suite">
        <el-select v-model="form.suite_id" placeholder="Select suite" clearable>
          <el-option v-for="s in suites" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
      </el-form-item>
    </el-form>

    <StepEditor v-model="form.steps" />

    <div style="margin-top:16px;display:flex;gap:8px">
      <el-button type="primary" @click="save">Save</el-button>
      <el-button @click="record">Record</el-button>
      <el-button @click="playback">Playback</el-button>
      <el-button @click="back">Back</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { list as listSuites } from '@/api/suites'
import * as casesApi from '@/api/cases'
import StepEditor from '@/components/StepEditor.vue'
import type { Step } from '@/types'

const route = useRoute()
const router = useRouter()
const id = computed(() => Number(route.params.id) || 0)
const isNew = computed(() => !route.params.id || route.params.id === 'new')

const suites = ref<{ id: number; name: string }[]>([])
const form = ref({
  name: '',
  suite_id: undefined as number | undefined,
  steps: [] as Step[],
})

onMounted(async () => {
  suites.value = await listSuites()
  if (!isNew.value && id.value) {
    const c = await casesApi.get(id.value)
    form.value = { name: c.name, suite_id: c.suite_id, steps: c.steps || [] }
  }
})

async function save() {
  const p = { name: form.value.name, suite_id: form.value.suite_id, steps: form.value.steps }
  if (isNew.value) {
    await casesApi.create(p)
  } else {
    await casesApi.update(id.value, p)
  }
  router.push('/cases')
}

function record() { /* TODO T26-T28 */ }
function playback() { /* TODO T30 */ }
function back() { router.back() }
</script>
