export interface User {
  id: number
  email: string
  display_name: string | null
  provider: string
  is_active: boolean
  created_at: string
}

export interface Role {
  id: number
  name: string
}

export interface Suite {
  id: number
  name: string
  description: string
  owner_id: number | null
  created_at: string
  updated_at: string
}

export interface Case {
  id: number
  suite_id: number
  name: string
  tags: string[]
  steps: import('./step').Step[]
  owner_id: number | null
  created_at: string
  updated_at: string
}

export type ActionName = import('./step').ActionName
export type { Step } from './step'

export interface Run {
  id: number
  suite_id: number
  env: string
  browser: string
  status: string
  started_by: number | null
  started_at: string
  finished_at: string | null
  summary: Record<string, unknown>
  log_path: string | null
}

export interface Schedule {
  id: number
  suite_id: number
  name: string
  cron: string
  env: string
  browser: string
  enabled: boolean
  owner_id: number | null
  created_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  user: User
  token: string
}
