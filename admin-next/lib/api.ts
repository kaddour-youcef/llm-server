// Prefer browser-exposed env; fall back for dev
const GATEWAY_URL =
  process.env.NEXT_PUBLIC_GATEWAY_URL ||
  process.env.GATEWAY_URL ||
  "http://localhost:8080"

import type {
  ApiKey,
  CreateKeyRequest,
  CreateKeyResponse,
  Paginated,
  RequestLog,
  SortDir,
  UsageData,
  User,
  UserDetail,
  UpdateUser,
  CreateUser,
} from "@/lib/types"

export class ApiClient {
  private apiKey: string | null = null

  setApiKey(key: string) {
    this.apiKey = key
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const url = `${GATEWAY_URL}${endpoint}`
    const headers = {
      "Content-Type": "application/json",
      ...(this.apiKey && { "x-api-key": this.apiKey }),
      ...options.headers,
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      // Try to parse JSON error bodies from FastAPI and surface useful detail/message
      let message = `HTTP ${response.status}`
      try {
        const contentType = response.headers.get("content-type") || ""
        if (contentType.includes("application/json")) {
          const data = await response.json()
          message = data?.detail || data?.error || data?.message || message
        } else {
          const text = await response.text()
          message = text || message
        }
      } catch {
        // ignore parse errors; keep default message
      }
      throw new Error(message)
    }

    return response.json()
  }

  // Auth validation
  async validateKey() {
    return this.request("/admin/users")
  }

  // Users
  async getUsers(params?: { page?: number; page_size?: number; sort_by?: string; sort_dir?: SortDir; q?: string }): Promise<Paginated<User>> {
    const search = new URLSearchParams()
    if (params?.page) search.set("page", String(params.page))
    if (params?.page_size) search.set("page_size", String(params.page_size))
    if (params?.sort_by) search.set("sort_by", params.sort_by)
    if (params?.sort_dir) search.set("sort_dir", params.sort_dir)
    if (params?.q) search.set("q", params.q)
    const qs = search.toString()
    return this.request(`/admin/users${qs ? `?${qs}` : ""}`)
  }

  async createUser(data: CreateUser): Promise<User> {
    return this.request("/admin/users", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async getUser(userId: string): Promise<UserDetail> {
    return this.request(`/admin/users/${userId}`)
  }

  async updateUser(userId: string, data: UpdateUser): Promise<User> {
    return this.request(`/admin/users/${userId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    })
  }

  // API Keys
  async getKeys(params?: {
    page?: number
    page_size?: number
    sort_by?: string
    sort_dir?: SortDir
    status?: "active" | "revoked"
    q?: string
  }): Promise<Paginated<ApiKey>> {
    const search = new URLSearchParams()
    if (params?.page) search.set("page", String(params.page))
    if (params?.page_size) search.set("page_size", String(params.page_size))
    if (params?.sort_by) search.set("sort_by", params.sort_by)
    if (params?.sort_dir) search.set("sort_dir", params.sort_dir)
    if (params?.status) search.set("status", params.status)
    if (params?.q) search.set("q", params.q)
    const qs = search.toString()
    return this.request(`/admin/keys${qs ? `?${qs}` : ""}`)
  }

  async createKey(data: CreateKeyRequest): Promise<CreateKeyResponse> {
    return this.request("/admin/keys", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async revokeKey(keyId: string): Promise<ApiKey> {
    return this.request(`/admin/keys/${keyId}/revoke`, {
      method: "POST",
    })
  }

  async rotateKey(keyId: string): Promise<CreateKeyResponse> {
    return this.request(`/admin/keys/${keyId}/rotate`, {
      method: "POST",
    })
  }

  // Usage
  async getUsage(params: { from: string; to: string; key_id?: string }): Promise<UsageData> {
    const searchParams = new URLSearchParams(params)
    return this.request(`/admin/usage?${searchParams}`)
  }

  // Requests
  async getRequests(): Promise<RequestLog[] | RequestLog> {
    return this.request("/admin/requests")
  }
}

export const apiClient = new ApiClient()
