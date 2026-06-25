<template>
  <div>
    <h3>Playback</h3>
    <el-select v-model="selectedCase" placeholder="Select case" @change="loadCase" class="playback-select">
      <el-option v-for="c in cases" :key="c.id" :value="c.id" :label="c.name" />
    </el-select>
    <el-button type="primary" @click="run" :disabled="!selectedCase || loading">Run Playback</el-button>
    <div v-if="result" class="playback-result">
      <el-tag :type="result.status === 'passed' ? 'success' : 'danger'">{{ result.status }}</el-tag>
      <pre class="playback-stdout">{{ result.stdout }}</pre>
      <div v-if="result.stderr" class="playback-stderr">{{ result.stderr }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { list } from '@/api/cases'
import type { Case } from '@/types'

const selectedCase = ref<number | null>(null)
const loading = ref(false)
const result = ref<any>(null)
const { data: cases } = useQuery({ queryKey: ['cases'], queryFn: () => list() })

async function loadCase() { result.value = null }
async function run() {
  loading.value = true
  const ws = new WebSocket(`ws://${location.host}/ws/playback`)
  const caseList = cases.value ?? []
  ws.onopen = () => ws.send(JSON.stringify({ action: 'start', case_name: caseList.find((c: Case) => c.id === selectedCase.value)?.name || 'unnamed', steps: [], browser: 'chromium' }))
  ws.onmessage = (e) => { const msg = JSON.parse(e.data); if (msg.type === 'done') { result.value = msg; loading.value = false } }
  ws.onerror = () => { loading.value = false }
}
</script>

<style scoped>
.playback-select {
  width: 320px;
}

.playback-result {
  margin-top: 12px;
}

.playback-stdout {
  background: var(--app-terminal-bg);
  color: var(--app-terminal-fg);
  padding: 8px;
  max-height: 300px;
  overflow: auto;
  font-family: Consolas, monospace;
  font-size: 12px;
  border-radius: 4px;
}

.playback-stderr {
  color: var(--app-terminal-fail);
}
