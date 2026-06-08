import { describe, it, expect } from 'vitest'

describe('router', () => {
  it('has login route as guest', async () => {
    const { default: router } = await import('@/router')
    const login = router.getRoutes().find((r) => r.name === 'Login')
    expect(login).toBeDefined()
    expect(login?.meta?.guest).toBe(true)
  })

  it('has dashboard route with auth guard', async () => {
    const { default: router } = await import('@/router')
    const dash = router.getRoutes().find((r) => r.name === 'Dashboard')
    expect(dash).toBeDefined()
    expect(dash?.meta?.requiresAuth).toBe(true)
  })
})
