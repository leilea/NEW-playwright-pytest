<template>
  <div class="case-editor">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
      <div style="display:flex;align-items:center;gap:8px">
        <h2 style="margin:0">{{ isNew ? '新建用例' : `用例: ${form.name || '加载中...'}` }}</h2>
        <el-tag v-if="!isNew && suiteName" size="small" type="info">{{ suiteName }}</el-tag>
      </div>
      <div style="display:flex;gap:8px">
        <el-button @click="back">返回</el-button>
        <el-button v-if="!isNew" type="success" @click="playback" :loading="playing">
          {{ playing ? '回放中...' : '回放' }}
        </el-button>
        <el-button type="primary" @click="save" :loading="saving">保存</el-button>
      </div>
    </div>

    <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px">
      <span style="color:var(--el-text-color-regular);font-size:14px">所属系统：</span>
      <template v-if="!isNew">
        <span style="font-weight:500">{{ suiteName || '—' }}</span>
      </template>
      <template v-if="isNew">
        <el-select v-model="form.suite_id" placeholder="选择系统" style="width:320px">
          <el-option v-for="s in suites" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
      </template>
    </div>

    <ParameterConfig v-model="form.parameters" />

    <el-tabs v-model="activeTab" style="margin-top:8px">
      <el-tab-pane label="操作步骤" name="steps">
        <StepEditor v-model="form.steps" />
      </el-tab-pane>

      <el-tab-pane label="生成脚本" name="script">
        <div v-if="scriptLoading" style="color:var(--el-text-color-secondary)">加载中...</div>
        <div v-else style="position:relative">
          <pre class="script-preview"><code>{{ script || '暂无步骤' }}</code></pre>
          <el-button
            v-if="script"
            size="small"
            text
            style="position:absolute;top:8px;right:8px"
            @click="copyScript"
          >
            {{ copied ? '已复制' : '复制脚本' }}
          </el-button>
        </div>
      </el-tab-pane>

      <el-tab-pane name="result">
        <template #label>
          <span>回放结果<el-badge v-if="playbackResult" style="margin-left:6px" :value="playbackResult.status === 'passed' ? '通过' : '失败'" :type="playbackResult.status === 'passed' ? 'success' : 'danger'" /></span>
        </template>
        <template v-if="playbackResult">
          <el-alert
            :title="playbackResult.status === 'passed' ? '通过' : '失败'"
            :type="playbackResult.status === 'passed' ? 'success' : 'error'"
            :closable="false"
            style="margin-bottom:8px"
          />
          <div style="display:flex;gap:8px;margin-bottom:8px">
            <el-tag size="small">exit code: {{ playbackResult.rc }}</el-tag>
            <el-tag v-if="playbackResult.screenshot" size="small" type="info">screenshot: {{ playbackResult.screenshot }}</el-tag>
          </div>
          <div v-if="playbackResult.stdout" style="margin-bottom:8px">
            <div style="font-weight:600;font-size:13px;margin-bottom:2px">STDOUT</div>
            <pre class="script-preview"><code>{{ playbackResult.stdout }}</code></pre>
          </div>
          <div v-if="playbackResult.stderr" style="margin-bottom:8px">
            <div style="font-weight:600;font-size:13px;margin-bottom:2px;color:var(--el-color-danger)">STDERR</div>
            <pre class="script-preview" style="color:var(--el-color-danger);border-color:var(--el-color-danger-light)"><code>{{ playbackResult.stderr }}</code></pre>
          </div>
        </template>
        <el-empty v-else description="暂无回放结果，点击「回放」按钮执行" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { list as listSuites } from '@/api/suites'
import * as casesApi from '@/api/cases'
import StepEditor from '@/components/StepEditor.vue'
import ParameterConfig from '@/components/ParameterConfig.vue'
import type { Step } from '@/types/step'
import type { Parameter } from '@/types'

const route = useRoute()
const router = useRouter()

const id = computed(() => route.params.id as string)
const isNew = computed(() => id.value === 'new')
const suiteIdFromQuery = computed(() => Number(route.query.suite_id) || 0)

const suites = ref<{ id: number; name: string }[]>([])
const suiteName = computed(() => suites.value.find(s => s.id === form.value.suite_id)?.name || '')

const form = ref({
  name: '',
  suite_id: 0,
  steps: [] as Step[],
  parameters: [] as Parameter[],
})

const activeTab = ref('steps')
const script = ref('')
const scriptLoading = ref(false)
const copied = ref(false)
const saving = ref(false)
const playing = ref(false)
const playbackResult = ref<null | {
  status: string; stdout: string; stderr: string; rc: number; screenshot?: string;
}>(null)

onMounted(async () => {
  suites.value = await listSuites()

  if (isNew.value) {
    form.value.suite_id = suiteIdFromQuery.value
  } else {
    const caseId = Number(id.value)
    if (caseId) {
      const c = await casesApi.get(caseId)
      form.value = {
        name: c.name,
        suite_id: c.suite_id,
        steps: (c.steps || []) as Step[],
        parameters: (c.parameters || []) as Parameter[],
      }
      loadScript(caseId)
    }
  }
})

watch(() => form.value.steps, () => {
  if (!isNew.value) {
    const caseId = Number(id.value)
    if (caseId) loadScript(caseId)
  }
}, { deep: true })

async function loadScript(caseId: number) {
  scriptLoading.value = true
  try {
    script.value = await casesApi.getScript(caseId)
  } catch {
    script.value = '无法加载脚本'
  }
  scriptLoading.value = false
}

function replaceParams(text: string): string {
  if (!text) return text
  for (const p of form.value.parameters) {
    if (!p.key) continue
    text = text.replace(new RegExp('\\{\\{' + escapeRegExp(p.key) + '\\}\\}', 'g'), p.value)
    const wordBoundary = '(?<![\\w])' + escapeRegExp(p.key) + '(?![\\w])'
    text = text.replace(new RegExp(wordBoundary, 'g'), p.value)
  }
  const now = new Date()
  text = text.replace(/\{\{random:(\d+)\}\}/g, (_, n) => String(Math.random()).slice(2, 2 + parseInt(n)))
  text = text.replace(/\{\{randomStr:(\d+)\}\}/g, (_, n) => Math.random().toString(36).slice(2, 2 + parseInt(n)))
  text = text.replace(/\{\{date\}\}/g, now.toISOString().slice(0, 10))
  text = text.replace(/\{\{time\}\}/g, now.toTimeString().slice(0, 5))
  text = text.replace(/\{\{datetime\}\}/g, now.toISOString().replace('T', ' ').slice(0, 16))
  text = text.replace(/\{\{timestamp\}\}/g, String(Date.now()))
  text = text.replace(/\{\{timeAdd:h\+(\d+)\}\}/g, (_, n) => new Date(now.getTime() + parseInt(n) * 3600000).toTimeString().slice(0, 5))
  text = text.replace(/\{\{timeSub:h\+(\d+)\}\}/g, (_, n) => new Date(now.getTime() - parseInt(n) * 3600000).toTimeString().slice(0, 5))
  text = text.replace(/\{\{dateAdd:d\+(\d+)\}\}/g, (_, n) => new Date(now.getTime() + parseInt(n) * 86400000).toISOString().slice(0, 10))
  text = text.replace(/\{\{dateSub:d\+(\d+)\}\}/g, (_, n) => new Date(now.getTime() - parseInt(n) * 86400000).toISOString().slice(0, 10))
  return text
}

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

async function save() {
  saving.value = true
  try {
    const payload = { name: form.value.name, suite_id: form.value.suite_id, steps: form.value.steps, parameters: form.value.parameters }
    if (isNew.value) {
      await casesApi.create(payload)
      ElMessage.success('用例已创建')
      router.push(`/suites/${form.value.suite_id}`)
    } else {
      await casesApi.update(Number(id.value), payload)
      ElMessage.success('已保存')
      loadScript(Number(id.value))
    }
  } catch (err: unknown) {
    ElMessage.error(`保存失败: ${err}`)
  }
  saving.value = false
}

function playback() {
  playing.value = true
  playbackResult.value = null
  activeTab.value = 'result'
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${proto}//${location.host}/ws/playback`)

  ws.onopen = () => {
    const resolvedSteps = form.value.steps.map((s: Step) => {
      const resolved: Record<string, unknown> = {}
      for (const [k, v] of Object.entries(s)) {
        resolved[k] = typeof v === 'string' ? replaceParams(v) : v
      }
      return resolved
    })
    ws.send(JSON.stringify({
      action: 'start',
      case_name: form.value.name,
      steps: resolvedSteps,
      browser: 'chromium',
    }))
  }

  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data)
    if (msg.type === 'done') {
      playbackResult.value = {
        status: msg.status,
        stdout: msg.stdout || '',
        stderr: msg.stderr || '',
        rc: msg.rc,
        screenshot: msg.screenshot,
      }
      playing.value = false
    } else if (msg.type === 'error') {
      playbackResult.value = {
        status: 'error',
        stdout: '',
        stderr: msg.text || '回放异常',
        rc: -1,
      }
      playing.value = false
    }
  }

  ws.onerror = () => {
    playbackResult.value = {
      status: 'error',
      stdout: '',
      stderr: 'WebSocket 连接失败',
      rc: -1,
    }
    playing.value = false
  }

  ws.onclose = () => { playing.value = false }
}

async function copyScript() {
  try {
    await navigator.clipboard.writeText(script.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    ElMessage.warning('复制失败，请手动选择复制')
  }
}

function back() {
  const sid = form.value.suite_id || suiteIdFromQuery.value
  if (sid) {
    router.push(`/suites/${sid}`)
  } else {
    router.push('/suites')
  }
}
</script>

<style scoped>
.script-preview {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px 16px;
  border-radius: 6px;
  font-family: 'Cascadia Code', 'Fira Code', monospace;
  font-size: 13px;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  border: 1px solid var(--el-border-color-light);
}

.script-preview code {
  background: none;
  padding: 0;
}
</style>
