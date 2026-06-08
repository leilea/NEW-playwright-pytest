<template>
  <div class="config-page">
    <h2>System Configuration (.env)</h2>
    <el-alert type="warning" :closable="false" show-icon style="margin-bottom:16px">
      Editing this file directly affects all running services. Restart backend for changes to take full effect.
    </el-alert>
    <el-input
      v-model="content"
      type="textarea"
      :rows="20"
      placeholder="# Environment variables..."
      style="font-family:monospace"
    />
    <el-button type="primary" :loading="saving" @click="save" style="margin-top:12px">Save</el-button>
    <el-tag v-if="saved" type="success" style="margin-left:8px">Saved</el-tag>
    <el-tag v-if="errorMsg" type="danger" style="margin-left:8px">{{ errorMsg }}</el-tag>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const apiUrl = import.meta.env.VITE_API_BASE || ''
const content = ref('')
const saving = ref(false)
const saved = ref(false)
const errorMsg = ref('')

async function load() {
  try {
    const r = await fetch(apiUrl + '/api/config/env')
    const data = await r.json()
    content.value = data.content || ''
  } catch (e) {
    errorMsg.value = 'Failed to load config'
  }
}

async function save() {
  saving.value = true
  saved.value = false
  errorMsg.value = ''
  try {
    const r = await fetch(apiUrl + '/api/config/env', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: content.value }),
    })
    if (r.ok) saved.value = true
    else errorMsg.value = 'Save failed'
  } catch {
    errorMsg.value = 'Save failed'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
