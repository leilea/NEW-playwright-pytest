import { http } from './client'
export interface Suite { id: number; name: string; description: string; owner_id: number | null; created_at: string }
export const list = () => http.get<Suite[]>('/suites').then(r => r.data)
export const create = (b: { name: string; description?: string }) => http.post<Suite>('/suites', b).then(r => r.data)
export const update = (id: number, b: { name: string; description?: string }) => http.put<Suite>(`/suites/${id}`, b).then(r => r.data)
export const remove = (id: number) => http.delete(`/suites/${id}`).then(r => r.data)
