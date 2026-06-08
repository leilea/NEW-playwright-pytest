import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/pages/Dashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/suites',
    name: 'Suites',
    component: () => import('@/pages/Suites.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/suites/:id',
    name: 'SuiteDetail',
    component: () => import('@/pages/SuiteDetail.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/cases',
    name: 'Cases',
    component: () => import('@/pages/Cases.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/cases/:id',
    name: 'CaseEditor',
    component: () => import('@/pages/CaseEditor.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/runs',
    name: 'Runs',
    component: () => import('@/pages/Runs.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/runs/:id',
    name: 'RunDetail',
    component: () => import('@/pages/RunDetail.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/pages/Reports.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/schedules',
    name: 'Schedules',
    component: () => import('@/pages/Schedules.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/config',
    name: 'Config',
    component: () => import('@/pages/Config.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
