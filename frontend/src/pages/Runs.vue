<template>
  <div class="runs-page">
    <h2>Test Runs</h2>

    <el-card style="margin-bottom:16px">
      <el-form :inline="true">
        <el-form-item label="Suite">
          <el-select v-model="suiteId" placeholder="Select suite" clearable @change="loadCases">
            <el-option v-for="s in suites" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Environment">
          <el-select v-model="env">
            <el-option label="dev" value="dev" />
            <el-option label="test" value="test" />
            <el-option label="staging" value="staging" />
            <el-option label="prod" value="prod" />
          </el-select>
        </el-form-item>
        <el-form-item label="Browser">
          <el-select v-model="browser">
            <el-option label="Chromium" value="chromium" />
            <el-option label="Firefox" value="firefox" />
            <el-option label="WebKit" value="webkit" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="starting" @click="startRun">Start Run</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="activeRunId">
      <template #header>Run #{{ activeRunId }}</template>
      <LogStream :raw="logBuffer" />
      <el-button v-if="runFinished" type="success" style="margin-top:8px" @click="viewAllure">View Allure Report</el-button>
    </el-card>

    <el-card style="margin-top:16px">
      <template #header>Run History</template>
      <el-table :data="runs" max-height="40vh">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="status" label="Status" width="100">
          <template #default="{ row }"><el-tag :type="statusTag(row.status)">{{ row.status }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="env" label="Env" width="80" />
        <el-table-column prop="browser" label="Browser" width="100" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { useWS } from '../composables/useWS'
import LogStream from '../components/LogStream.vue'

const apiBase = import.meta.env.VITE_API_BASE || ''
const wsBase = import.meta.env.VITE_WS_BASE || 'ws://localhost:8000'

const suites = ref<any[]>([])
const suiteId = ref<number | null>(null)
const env = ref('test')
const browser = ref('chromium')
const starting = ref(false)
const runs = ref<any[]>([])
const activeRunId = ref<number | null>(null)
const logBuffer = ref('')
const runFinished = ref(false)

const wsUrl = computed(() => activeRunId.value ? `${wsBase}/ws/run/${activeRunId.value}` : null)

const { connected, close } = useWS(
  () => wsUrl.value,
  {
    onMessage(text) {
      logBuffer.value += text + '\n'
      if (text.includes('= 1 passed') || text.includes('= 1 failed') || text.includes('= 1 error')) {
        runFinished.value = true
      }
    },
    onClose() { runFinished.value = true },
  }
)

async function loadSuites() {
  try {
    const r = await fetch(apiBase + '/api/suites')
    suites.value = await r.json()
  } catch {}
}

async function loadRuns() {
  try {
    const r = await fetch(apiBase + '/api/runs')
    runs.value = await r.json()
  } catch {}
}

async function loadCases() {}

async function startRun() {
  if (!suiteId.value) return
  starting.value = true
  logBuffer.value = ''
  runFinished.value = false
  try {
    const r = await fetch(apiBase + '/api/runs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        suite_id: suiteId.value,
        env: env.value,
        browser: browser.value,
      }),
    })
    const run = await r.json()
    activeRunId.value = run.id
    loadRuns()
  } catch {} finally {
    starting.value = false
  }
}

function statusTag(s: string) {
  if (s === 'passed') return 'success'
  if (s === 'failed' || s === 'error') return 'danger'
  if (s === 'running') return 'warning'
  return 'info'
}

function viewAllure() {
  window.open(apiBase + '/api/reports/raw/allure-results/index.html', '_blank')
}

loadSuites()
loadRuns()
</script>
