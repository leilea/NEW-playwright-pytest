import { api } from './client'

export type Role = 'admin' | 'editor' | 'viewer'
export interface User { id: number; email: string; display_name: string | null; roles: Role[] }

export const login = (email: string, password: string) =>
  api.post<{ access_token: string; token_type: string }>('/auth/login', { email, password }).then((r: any) => r.data)

export const fetchMe = () => api.get<User>('/auth/me').then((r: any) => r.data)

export const logout = () => api.post('/auth/logout').then((r: any) => r.data)
