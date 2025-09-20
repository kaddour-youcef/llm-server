// Centralized domain types for the Admin Next.js app.
// Mirrors Gateway API shapes to ensure type safety across the boundary.

export type SortDir = "asc" | "desc"

export interface Paginated<T> {
  items: T[]
  page?: number | null
  page_size?: number | null
  total: number
}

export type ApiKeyRole = "user" | "admin"
export type ApiKeyStatus = "active" | "revoked"

export interface User {
  id: string
  name: string
  email?: string | null
  status?: "pending" | "approved" | "disabled" | null
  created_at?: string | null
}

export interface ApiKey {
  id: string
  user_id: string
  name: string
  role: ApiKeyRole
  status: ApiKeyStatus
  last4?: string
  monthly_quota_tokens?: number | null
  daily_request_quota?: number | null
  created_at?: string | null
}

export interface UserDetail extends Omit<User, "created_at"> {
  created_at?: string | null
  keys: ApiKey[]
}

export interface CreateUser {
  name: string
  email?: string
}

export interface UpdateUser {
  name?: string
  email?: string
  status?: "pending" | "approved" | "disabled"
}

export interface CreateKeyRequest {
  user_id: string
  name: string
  role: ApiKeyRole
  monthly_quota_tokens?: number | null
  daily_request_quota?: number | null
}

export interface CreateKeyResponse {
  id: string
  user_id: string
  name: string
  role: ApiKeyRole
  status: ApiKeyStatus
  last4: string
  plaintext_key?: string
}

export interface RequestLog {
  id?: string
  timestamp?: string
  method?: string
  endpoint?: string
  status_code?: number
  response_time_ms?: number
  user_id?: string
  key_id?: string
  tokens_used?: number
  error_message?: string
  request_body?: string
  response_body?: string
}

export interface UsageData {
  totals: {
    total_tokens: number
    request_count: number
  }
  timeseries: Array<{
    day: string
    total_tokens: number
    request_count: number
  }>
}
