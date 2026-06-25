import type { Case, Step as StepType } from '@/types'
import api from './client'

export type { Case } from '@/types'

export async function list(suiteId?: number): Promise<Case[]> {
  const params = suiteId ? { suite_id: suiteId } : {}
  const { data } = await api.get('/cases', { params })
  return data
}

export async function get(id: number): Promise<Case> {
  const { data } = await api.get(`/cases/${id}`)
  return data
}

export async function create(payload: Partial<Case>): Promise<Case> {
  const { data } = await api.post('/cases', payload)
  return data
}

export async function update(id: number, payload: Partial<Case>): Promise<Case> {
  const { data } = await api.put(`/cases/${id}`, payload)
  return data
}

export async function remove(id: number): Promise<void> {
  await api.delete(`/cases/${id}`)
}

export async function getScript(id: number, browser = 'chromium'): Promise<string> {
  const { data } = await api.get(`/cases/${id}/script`, { params: { browser } })
  return data.script
}
