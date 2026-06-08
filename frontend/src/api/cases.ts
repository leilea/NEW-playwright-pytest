import { http } from './client'
import type { Step } from '@/types/step'
export interface Case { id: number; suite_id: number; name: string; tags: string[]; steps: Step[]; owner_id: number | null; created_at: string; updated_at: string }
export const list = (suiteId?: number) => http.get<Case[]>('/cases', { params: suiteId ? { suite_id: suiteId } : {} }).then(r => r.data)
export const get = (id: number) => http.get<Case>(`/cases/${id}`).then(r => r.data)
export const create = (b: { suite_id: number; name: string; tags?: string[]; steps?: Step[] }) => http.post<Case>('/cases', b).then(r => r.data)
export const update = (id: number, b: { name?: string; tags?: string[]; steps?: Step[] }) => http.put<Case>(`/cases/${id}`, b).then(r => r.data)
export const remove = (id: number) => http.delete(`/cases/${id}`).then(r => r.data)
