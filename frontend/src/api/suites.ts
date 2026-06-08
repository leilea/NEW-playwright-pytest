import { api } from './client'
export interface Suite { id: number; name: string; description: string; owner_id: number | null; created_at: string }
export const list = () => api.get<Suite[]>('/suites').then((r: any) => r.data)
export const create = (b: { name: string; description?: string }) => api.post<Suite>('/suites', b).then((r: any) => r.data)
export const update = (id: number, b: { name: string; description?: string }) => api.put<Suite>(`/suites/${id}`, b).then((r: any) => r.data)
export const remove = (id: number) => api.delete(`/suites/${id}`).then((r: any) => r.data)
