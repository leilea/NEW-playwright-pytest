import { api } from './client'
export interface Suite { id: number; name: string; version: string; description: string; owner_id: number | null; created_at: string; case_count: number }
export const list = () => api.get<Suite[]>('/suites').then((r: any) => r.data)
export const get = (id: number) => api.get<Suite>(`/suites/${id}`).then((r: any) => r.data)
export const create = (b: { name: string; version?: string; description?: string }) => api.post<Suite>('/suites', b).then((r: any) => r.data)
export const update = (id: number, b: { name: string; version?: string; description?: string }) => api.put<Suite>(`/suites/${id}`, b).then((r: any) => r.data)
export const remove = (id: number) => api.delete(`/suites/${id}`).then((r: any) => r.data)
