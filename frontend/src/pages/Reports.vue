<template>
  <div class="reports-page">
    <h2>Reports</h2>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="Allure" name="allure">
        <iframe
          v-if="allureUrl"
          :src="allureUrl"
          style="width:100%; height:80vh; border:none"
        />
        <el-empty v-else description="No Allure report" />
      </el-tab-pane>
      <el-tab-pane label="HTML" name="html">
        <el-table :data="htmlFiles" max-height="72vh">
          <el-table-column prop="name" label="File" />
          <el-table-column prop="size" label="Size">
            <template #default="{ row }">{{ (row.size / 1024).toFixed(1) }} KB</template>
          </el-table-column>
          <el-table-column label="Action">
            <template #default="{ row }">
              <el-button size="small" @click="openFile(row)">Open</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="Screenshots" name="screenshots">
        <div class="screenshot-grid">
          <div v-for="f in imageFiles" :key="f.name" class="screenshot-card">
            <el-image :src="apiUrl + '/api/reports/raw/' + f.path" fit="contain" style="width:240px;height:160px" />
            <p>{{ f.name }}</p>
          </div>
          <el-empty v-if="!imageFiles.length" description="No screenshots" />
        </div>
      </el-tab-pane>
      <el-tab-pane label="Logs" name="logs">
        <pre v-if="selectedLog" class="log-viewer">{{ selectedLog }}</pre>
        <el-table v-else :data="logFiles" max-height="70vh" @row-click="fetchLog">
          <el-table-column prop="name" label="Log" />
          <el-table-column prop="size" label="Size">
            <template #default="{ row }">{{ (row.size / 1024).toFixed(1) }} KB</template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const apiUrl = import.meta.env.VITE_API_BASE || ''
const activeTab = ref('allure')
const files = ref<any[]>([])
const selectedLog = ref('')

const allureUrl = computed(() =>
  files.value.some(f => f.name === 'index.html' && f.path.includes('allure'))
    ? apiUrl + '/api/reports/raw/allure-results/index.html'
    : null
)

const htmlFiles = computed(() => files.value.filter(f => f.name.endsWith('.html')))
const imageFiles = computed(() => files.value.filter(f => /\.(png|jpg|jpeg|gif|webp)$/i.test(f.name)))
const logFiles = computed(() => files.value.filter(f => f.name.endsWith('.log')))

async function loadFiles() {
  try {
    const r = await fetch(apiUrl + '/api/reports/files')
    files.value = await r.json()
  } catch {}
}

function openFile(row: any) {
  window.open(apiUrl + '/api/reports/raw/' + row.path, '_blank')
}

async function fetchLog(row: any) {
  try {
    const r = await fetch(apiUrl + '/api/reports/raw/' + row.path)
    selectedLog.value = await r.text()
  } catch {}
}

onMounted(loadFiles)
</script>

<style scoped>
.screenshot-grid { display:flex; flex-wrap:wrap; gap:12px }
.screenshot-card { text-align:center; width:250px }
.log-viewer { background:#1e1e1e; color:#d4d4d4; padding:16px; max-height:70vh; overflow:auto; font-size:12px; white-space:pre-wrap }
</style>
