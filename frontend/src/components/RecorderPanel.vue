<template>
  <div class="recorder-panel">
    <div class="recorder-toolbar">
      <el-input
        v-model="url"
        placeholder="Target URL"
        class="recorder-url-input"
        disabled
      />
      <el-button type="primary" @click="start" :loading="running">
        {{ running ? '录制中...' : '开始录制' }}
      </el-button>
      <el-button v-if="running" type="danger" @click="stop">录制结束</el-button>
    </div>

    <el-alert v-if="error" :title="error" type="error" closable @close="error = ''" class="recorder-alert" />

    <div v-if="recordedSteps.length > 0 || running" class="recorder-steps">
      <div class="recorder-steps-title">
        录制步骤 ({{ recordedSteps.length }})
      </div>
      <div ref="logRef" class="recorder-log">
        <div v-if="running" class="recorder-recording">⏺ 录制中...</div>
        <div v-for="(s,i) in recordedSteps" :key="i" class="recorder-step">
          #{{ i + 1 }} {{ s.action }}: {{ formatParams(s) }}
        </div>
      </div>
    </div>

    <div v-if="recordedSteps.length > 0 && !running" class="recorder-save-row">
      <el-input v-model="caseName" placeholder="输入用例名称" class="recorder-case-input" />
      <el-button type="success" :disabled="!caseName" @click="saveCase">生成用例</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { api } from '@/api/client'
import type { Step, ActionName } from '@/types/step'

const emit = defineEmits<{
  'create-case': [payload: { name: string; steps: Step[]; url: string }]
}>()

const url = ref('')
const running = ref(false)
const error = ref('')
const recordedSteps = ref<Step[]>([])
const caseName = ref('')
const logRef = ref<HTMLElement | null>(null)
let ws: WebSocket | null = null

watch(recordedSteps, async () => {
  await nextTick()
  logRef.value?.scrollTo(0, logRef.value.scrollHeight)
})

function formatParams(step: Step): string {
  return Object.entries(step)
    .filter(([k, v]) => k !== 'seq' && k !== 'action' && v !== '' && v !== undefined)
    .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
    .join(', ')
}

function start() {
  const targetUrl = url.value
  if (!targetUrl) return
  ws?.close()
  ws = null
  error.value = ''
  recordedSteps.value = []
  caseName.value = ''
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${proto}//${location.host}/ws/rec`)
  ws.onopen = () => {
    ws!.send(JSON.stringify({ cmd: 'start', url: targetUrl }))
  }
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data)
    if (msg.event === 'step') {
      const s = msg.step as { action: string; params: Record<string, string | number> }
      const stepObj = { seq: recordedSteps.value.length + 1, action: s.action as ActionName, ...s.params } as Step
      console.log(`[FE] STEP #${stepObj.seq} ${stepObj.action}:`, JSON.stringify(stepObj))
      recordedSteps.value = [...recordedSteps.value, stepObj]
    } else if (msg.event === 'done') {
      console.log('[FE] DONE (total steps:', recordedSteps.value.length, ')')
    } else if (msg.event === 'error') {
      running.value = false
    } else if (msg.event === 'error') {
      error.value = msg.message || '录制错误'
    }
  }
  ws.onerror = () => { error.value = 'WebSocket 连接错误'; running.value = false }
  ws.onclose = () => { running.value = false }
  running.value = true
}

function stop() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ cmd: 'stop' }))
  }
}

onMounted(async () => {
  try {
    const { data } = await api.get('/config/recording-url')
    url.value = data.url
  } catch {
    url.value = 'https://dsep-portal-test.minmetals.com.cn/portal/signin'
  }
})

onUnmounted(() => {
  if (ws) {
    ws.close()
    ws = null
  }
})

function saveCase() {
  if (!caseName.value.trim()) return
  emit('create-case', {
    name: caseName.value.trim(),
    steps: recordedSteps.value,
    url: url.value,
  })
}
</script>

<style scoped>
.recorder-toolbar {
  margin-bottom: 12px;
  display: flex;
  gap: 8px;
  align-items: center;
}

.recorder-url-input {
  width: 480px;
}

.recorder-alert {
  margin-bottom: 8px;
}

.recorder-steps {
  margin-bottom: 12px;
}

.recorder-steps-title {
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--el-text-color-primary);
}

.recorder-log {
  background: var(--app-terminal-bg);
  color: var(--app-terminal-fg);
  padding: 8px;
  max-height: 220px;
  overflow: auto;
  font-family: Consolas, monospace;
  font-size: 12px;
  border-radius: 4px;
}

.recorder-recording {
  color: var(--el-color-primary-light-3);
  margin-bottom: 4px;
}

.recorder-step {
  color: var(--app-terminal-pass);
  margin-bottom: 2px;
}

.recorder-save-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.recorder-case-input {
  width: 240px;
}
</style>
