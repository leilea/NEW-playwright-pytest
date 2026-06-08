<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
</script>
<template>
  <div>
    <h2>仪表盘</h2>
    <p>欢迎，{{ auth.user?.email }}</p>
  </div>
</template>
