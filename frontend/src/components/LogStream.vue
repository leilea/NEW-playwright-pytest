<template>
  <div ref="containerRef" class="log-stream" @scroll="onUserScroll">
    <pre v-if="lines.length === 0" class="log-empty">Waiting for logs...</pre>
    <div v-for="(line, i) in lines" :key="i" class="log-line" :class="lineClass(line)" v-html="line"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'

const props = defineProps<{ raw: string }>()
const containerRef = ref<HTMLElement | null>(null)
const lines = ref<string[]>([])
const userScrolledUp = ref(false)

function lineClass(text: string) {
  if (text.includes('PASSED') || text.includes('passed')) return 'log-pass'
  if (text.includes('FAILED') || text.includes('ERROR') || text.includes('error')) return 'log-fail'
  if (text.includes('SKIPPED') || text.includes('WARN')) return 'log-skip'
  return ''
}

watch(() => props.raw, (val) => {
  if (!val) return
  lines.value = val.split('\n').map(l => escapeHtml(l))
  if (!userScrolledUp.value) scrollBottom()
})

function escapeHtml(s: string) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function scrollBottom() {
  nextTick(() => {
    const el = containerRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function onUserScroll() {
  const el = containerRef.value
  if (!el) return
  userScrolledUp.value = el.scrollTop + el.clientHeight < el.scrollHeight - 40
}
</script>

<style scoped>
.log-stream { background:var(--app-terminal-bg); color:var(--app-terminal-fg); padding:12px; max-height:60vh; overflow:auto; font:12px/1.5 Consolas,monospace; border-radius:4px }
.log-line { white-space:pre-wrap; word-break:break-all; min-height:18px }
.log-pass { color:var(--app-terminal-pass) }
.log-fail { color:var(--app-terminal-fail) }
.log-skip { color:var(--app-terminal-skip) }
.log-empty { color:var(--app-terminal-muted) }
</style>
