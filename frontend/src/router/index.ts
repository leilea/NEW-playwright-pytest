import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/pages/Dashboard.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'suites',
        name: 'Suites',
        component: () => import('@/pages/Suites.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'suites/:id',
        name: 'SuiteDetail',
        component: () => import('@/pages/SuiteDetail.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'cases/new',
        name: 'CaseNew',
        component: () => import('@/pages/CaseEditor.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'cases/:id',
        name: 'CaseEditor',
        component: () => import('@/pages/CaseEditor.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'runs',
        name: 'Runs',
        component: () => import('@/pages/Runs.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'runs/:id',
        name: 'RunDetail',
        component: () => import('@/pages/RunDetail.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'reports',
        name: 'Reports',
        component: () => import('@/pages/Reports.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'schedules',
        name: 'Schedules',
        component: () => import('@/pages/Schedules.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'config',
        name: 'Config',
        component: () => import('@/pages/Config.vue'),
        meta: { requiresAuth: true },
      },
    ],
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
    meta: { guest: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
