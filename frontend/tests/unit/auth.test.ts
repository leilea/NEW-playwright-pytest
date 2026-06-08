import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  fetchMe: vi.fn(),
  logout: vi.fn(),
}))

import * as api from '@/api/auth'

describe('auth store', () => {
  beforeEach(() => { setActivePinia(createPinia()) })

  it('login sets user and roles', async () => {
    vi.mocked(api.login).mockResolvedValue({ access_token: 't' } as any)
    vi.mocked(api.fetchMe).mockResolvedValue({ id: 1, email: 'a@b.c', display_name: 'A', roles: ['admin'] })
    const store = useAuthStore()
    await store.login('a@b.c', 'pw')
    expect(store.user?.email).toBe('a@b.c')
    expect(store.roles).toEqual(['admin'])
  })

  it('hasRole returns true for matching role', async () => {
    vi.mocked(api.fetchMe).mockResolvedValue({ id: 1, email: 'a@b.c', display_name: 'A', roles: ['editor'] })
    const store = useAuthStore()
    await store.refresh()
    expect(store.hasRole('editor')).toBe(true)
    expect(store.hasRole('admin')).toBe(false)
  })
})
