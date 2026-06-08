<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useQuery } from '@tanstack/vue-query'
import { list as listCases } from '@/api/cases'
const route = useRoute()
const suiteId = Number(route.params.id)
const { data } = useQuery({ queryKey: ['cases', suiteId], queryFn: () => listCases(suiteId) })
</script>
<template>
  <h2>套件 #{{ suiteId }}</h2>
  <router-link :to="`/cases?suite=${suiteId}&new=1`">+ 新建用例</router-link>
  <el-table :data="data || []">
    <el-table-column prop="id" label="ID" width="60" />
    <el-table-column prop="name" label="名称" />
    <el-table-column prop="tags" label="标签" />
  </el-table>
</template>
