<template>
  <div class="config-page">
    <el-card class="config-card">
      <h3>录制目标地址</h3>
      <p class="config-desc">录制新用例时默认打开的初始页面 URL。</p>
      <el-input v-model="recUrl" placeholder="https://example.com/login" />
      <div class="config-actions">
        <el-button type="primary" :loading="urlSaving" @click="saveRecUrl">保存</el-button>
        <el-tag v-if="urlSaved" type="success">已保存</el-tag>
        <el-tag v-if="urlError" type="danger">{{ urlError }}</el-tag>
      </div>
    </el-card>

    <el-card class="config-card">
      <h2>System Configuration (.env)</h2>
      <el-alert type="warning" :closable="false" show-icon style="margin-bottom:16px">
        Editing this file directly affects all running services. Restart backend for changes to take full effect.
      </el-alert>
      <el-input
        v-model="envContent"
        type="textarea"
        :rows="20"
        placeholder="# Environment variables..."
        style="font-family:monospace"
      />
      <div class="config-actions">
        <el-button type="primary" :loading="envSaving" @click="saveEnv">Save</el-button>
        <el-tag v-if="envSaved" type="success">Saved</el-tag>
        <el-tag v-if="envError" type="danger">{{ envError }}</el-tag>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api/client'

const recUrl = ref('')
const urlSaving = ref(false)
const urlSaved = ref(false)
const urlError = ref('')

const envContent = ref('')
const envSaving = ref(false)
const envSaved = ref(false)
const envError = ref('')

const apiUrl = import.meta.env.VITE_API_BASE || ''

async function loadRecUrl() {
  try {
    const { data } = await api.get('/config/recording-url')
    recUrl.value = data.url
  } catch {
    urlError.value = 'Failed to load recording URL'
  }
}

async function saveRecUrl() {
  urlSaving.value = true
  urlSaved.value = false
  urlError.value = ''
  try {
    const { data } = await api.put('/config/recording-url', { url: recUrl.value })
    if (data.ok) urlSaved.value = true
    else urlError.value = 'Save failed'
  } catch {
    urlError.value = 'Save failed'
  } finally {
    urlSaving.value = false
  }
}

async function loadEnv() {
  try {
    const r = await fetch(apiUrl + '/api/config/env')
    const data = await r.json()
    envContent.value = data.content || ''
  } catch {
    envError.value = 'Failed to load config'
  }
}

async function saveEnv() {
  envSaving.value = true
  envSaved.value = false
  envError.value = ''
  try {
    const r = await fetch(apiUrl + '/api/config/env', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: envContent.value }),
    })
    if (r.ok) envSaved.value = true
    else envError.value = 'Save failed'
  } catch {
    envError.value = 'Save failed'
  } finally {
    envSaving.value = false
  }
}

onMounted(() => {
  loadRecUrl()
  loadEnv()
})
</script>

<style scoped>
.config-page {
  max-width: 800px;
  margin: 0 auto;
}
.config-card {
  margin-bottom: 24px;
}
.config-desc {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  margin: 4px 0 12px;
}
.config-actions {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
