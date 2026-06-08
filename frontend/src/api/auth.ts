import { http } from './client'

export type Role = 'admin' | 'editor' | 'viewer'
export interface User { id: number; email: string; display_name: string | null; roles: Role[] }

export const login = (email: string, password: string) =>
  http.post<{ access_token: string; token_type: string }>('/auth/login', { email, password }).then(r => r.data)

export const fetchMe = () => http.get<User>('/auth/me').then(r => r.data)

export const logout = () => http.post('/auth/logout').then(r => r.data)
