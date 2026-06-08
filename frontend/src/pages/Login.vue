<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const email = ref('admin@local')
const password = ref('admin123')
const loading = ref(false)
const error = ref('')
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

async function submit() {
  loading.value = true
  error.value = ''
  try {
    await auth.login(email.value, password.value)
    const next = (route.query.next as string) || '/'
    router.replace(next)
  } catch (e: any) {
    error.value = e?.response?.data?.detail || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <el-container style="height:100vh;align-items:center;justify-content:center;background:#f5f7fa">
    <el-card style="width:360px">
      <h2 style="text-align:center;margin-top:0">DSEP Test Platform</h2>
      <el-form @submit.prevent="submit">
        <el-form-item label="邮箱"><el-input v-model="email" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="password" type="password" show-password /></el-form-item>
        <el-button type="primary" :loading="loading" @click="submit" style="width:100%">登录</el-button>
        <el-alert v-if="error" :title="error" type="error" show-icon style="margin-top:12px" />
      </el-form>
    </el-card>
  </el-container>
</template>
