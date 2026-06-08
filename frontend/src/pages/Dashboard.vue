<script setup lang="ts">
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import EChart from '@/components/EChart.vue'
import { api } from '@/api/client'

const { data: sum } = useQuery({ queryKey: ['dash-summary'], queryFn: () => api.get('/dashboard/summary').then((r: any) => r.data) })
const { data: trends } = useQuery({ queryKey: ['dash-trends'], queryFn: () => api.get('/dashboard/trends').then((r: any) => r.data) })

const statusPie = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [{ type: 'pie', radius: ['40%', '70%'], data: Object.entries(sum.value?.status_distribution || {}).map(([k, v]) => ({ name: k, value: v })) }],
}))

const trendLine = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['passed', 'failed'] },
  xAxis: { type: 'category', data: (trends.value || []).map((t: { date: string }) => t.date) },
  yAxis: { type: 'value' },
  series: [
    { name: 'passed', type: 'line', data: (trends.value || []).map((t: { passed: number }) => t.passed) },
    { name: 'failed', type: 'line', data: (trends.value || []).map((t: { failed: number }) => t.failed) },
  ],
}))
</script>

<template>
  <h2>仪表盘</h2>
  <el-row :gutter="16">
    <el-col :span="6"><el-statistic title="套件数" :value="sum?.total_suites ?? 0" /></el-col>
    <el-col :span="6"><el-statistic title="用例数" :value="sum?.total_cases ?? 0" /></el-col>
    <el-col :span="6"><el-statistic title="24h 运行" :value="sum?.runs_24h ?? 0" /></el-col>
    <el-col :span="6"><el-statistic title="通过率" :value="sum?.pass_rate ?? 0" suffix="%" /></el-col>
  </el-row>
  <el-row :gutter="16" style="margin-top:16px">
    <el-col :span="12"><EChart :option="statusPie" /></el-col>
    <el-col :span="12"><EChart :option="trendLine" /></el-col>
  </el-row>
</template>
