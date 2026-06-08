<template>
  <div class="recorder-panel">
    <div style="margin-bottom:12px">
      <el-input v-model="url" placeholder="Target URL, e.g. https://dsep-portal-test.minmetals.com.cn/portal/signin" style="width:480px" />
      <el-button type="primary" @click="start" :loading="running" style="margin-left:8px">
        {{ running ? 'Recording...' : 'Start Recording' }}
      </el-button>
      <el-button v-if="running" @click="stop">Stop</el-button>
    </div>
    <el-alert v-if="error" :title="error" type="error" closable @close="error = ''" />
    <div ref="logRef" class="rec-log" style="background:#1e1e1e;color:#ccc;padding:8px;max-height:200px;overflow:auto;font-family:monospace;font-size:12px">
      <div v-for="(line,i) in log" :key="i">{{ line }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { Step, ActionName } from '@/types/step'

const emit = defineEmits<{
  step: [step: Step]
}>()

const url = ref('https://dsep-portal-test.minmetals.com.cn/portal/signin')
const running = ref(false)
const log = ref<string[]>([])
const error = ref('')
const logRef = ref<HTMLElement | null>(null)
let ws: WebSocket | null = null

watch(log, async () => { await nextTick(); logRef.value?.scrollTo(0, logRef.value.scrollHeight) })

function start() {
  if (!url.value) return
  error.value = ''
  log.value = ['Connecting...']
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${proto}//${location.host}/ws/rec`)
  ws.onopen = () => {
    log.value.push('WebSocket connected, starting codegen...')
    ws!.send(JSON.stringify({ action: 'start', url: url.value }))
  }
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data)
    if (msg.type === 'log') {
      log.value.push(msg.text)
      const parsed = parseLine(msg.text)
      if (parsed) emit('step', { seq: -1, action: parsed.action, params: parsed.params })
    } else if (msg.type === 'done') {
      log.value.push('Recording finished.')
      running.value = false
    } else if (msg.type === 'error') {
      error.value = msg.text
      running.value = false
    }
  }
  ws.onerror = () => { error.value = 'WebSocket error'; running.value = false }
  ws.onclose = () => { running.value = false }
  running.value = true
}

function stop() { if (ws) { ws.send(JSON.stringify({ action: 'stop' })); ws.close() } running.value = false }

const STEP_PATTERNS: [RegExp, ActionName][] = [
  [/page\.goto\s*\(\s*['"]([^'"]+)['"]/i, 'goto' as ActionName],
  [/page\.click\s*\(\s*['"]([^'"]+)['"]/i, 'click' as ActionName],
  [/page\.fill\s*\(\s*['"]([^'"]+)['"]\s*,\s*['"]([^'"]+)['"]/i, 'fill' as ActionName],
  [/page\.expect\s*\(\s*['"]([^'"]+)['"]\s*\)\s*\.toHaveText\s*\(\s*['"]([^'"]+)['"]/i, 'expect' as ActionName],
  [/page\.check\s*\(\s*['"]([^'"]+)['"]/i, 'check' as ActionName],
  [/page\.uncheck\s*\(\s*['"]([^'"]+)['"]/i, 'check' as ActionName],
  [/page\.selectOption\s*\(\s*['"]([^'"]+)['"]\s*,\s*['"]([^'"]+)['"]/i, 'select' as ActionName],
  [/page\.hover\s*\(\s*['"]([^'"]+)['"]/i, 'hover' as ActionName],
  [/page\.waitForTimeout\s*\(\s*(\d+)/i, 'wait' as ActionName],
  [/page\.screenshot\s*\(\s*\{[^}]*path\s*:\s*['"]([^'"]+)['"]/i, 'screenshot' as ActionName],
  [/page\.evaluate\s*\(\s*`([^`]+)`/i, 'eval' as ActionName],
]

function parseLine(line: string): Step | null {
  for (const [re, action] of STEP_PATTERNS) {
    const m = line.match(re)
    if (m) {
      if (action === 'fill') return { seq: -1, action, params: { selector: m[1], value: m[2] } }
      if (action === 'expect') return { seq: -1, action, params: { selector: m[1], text: m[2] } }
      if (action === 'select') return { seq: -1, action, params: { selector: m[1], value: m[2] } }
      if (action === 'wait') return { seq: -1, action, params: { ms: parseInt(m[1]) } }
      return { seq: -1, action, params: action === 'goto' ? { url: m[1] }
        : action === 'screenshot' ? { name: m[1] }
        : action === 'eval' ? { code: m[1] }
        : action === 'check' ? { selector: m[1], state: 'check' }
        : { selector: m[1] } }
    }
  }
  return null
}
</script>
