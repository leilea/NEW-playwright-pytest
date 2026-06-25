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
    const next = (route.query.next as string) || '/dashboard'
    router.replace(next)
  } catch (e: any) {
    error.value = e?.response?.data?.detail || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <el-container class="login-page">
    <el-card class="login-card">
      <h2 class="login-title">DSEP Test Platform</h2>
      <el-form @submit.prevent="submit">
        <el-form-item label="登录账号"><el-input v-model="email" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="password" type="password" show-password /></el-form-item>
        <el-button type="primary" :loading="loading" @click="submit" class="login-btn">登录</el-button>
        <el-alert v-if="error" :title="error" type="error" show-icon class="login-error" />
      </el-form>
    </el-card>
  </el-container>
</template>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--el-color-primary-light-9) 0%, var(--el-color-primary-light-7) 100%);
}

.login-card {
  width: 380px;
  border-radius: var(--el-border-radius-base);
}

.login-title {
  text-align: center;
  margin-top: 0;
  color: var(--el-color-primary);
  font-size: 20px;
}

.login-btn {
  width: 100%;
}

.login-error {
  margin-top: 12px;
}
</style>
