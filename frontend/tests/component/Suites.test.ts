import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { VueQueryPlugin } from '@tanstack/vue-query'
import ElementPlus from 'element-plus'

vi.mock('@/api/suites', () => ({
  list: vi.fn().mockResolvedValue([{ id: 1, name: 's1', description: 'd', owner_id: 1, created_at: '2026-01-01' }]),
  create: vi.fn(),
  remove: vi.fn(),
}))

import Suites from '@/pages/Suites.vue'

describe('Suites.vue', () => {
  it('renders list from api', async () => {
    setActivePinia(createPinia())
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/', component: { template: '<div/>' } }] })
    const w = mount(Suites, { global: { plugins: [router, VueQueryPlugin, ElementPlus] } })
    await new Promise(r => setTimeout(r, 0))
    expect(w.text()).toContain('s1')
  })
})
