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
  Organization,
  Team,
  Membership,
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

  // --- User (JWT) Endpoints for end-user portal ---
  async userRegister(data: { name: string; email: string; password: string }) {
    const res = await fetch(`${GATEWAY_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error((await res.json()).detail || "Registration failed")
    return res.json()
  }

  async userLogin(data: { email: string; password: string }) {
    const res = await fetch(`${GATEWAY_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(data),
      credentials: "include",
    })
    if (!res.ok) throw new Error((await res.json()).detail || "Login failed")
    return res.json() as Promise<{ access_token: string; refresh_token: string; token_type: string }>
  }

  async userRefresh(refreshToken: string) {
    const res = await fetch(`${GATEWAY_URL}/auth/refresh`, {
      method: "POST",
      headers: { Authorization: `Bearer ${refreshToken}` },
      credentials: "include",
    })
    if (!res.ok) throw new Error((await res.json()).detail || "Refresh failed")
    return res.json() as Promise<{ access_token: string; token_type: string }>
  }

  async userKeys(accessToken: string) {
    const res = await fetch(`${GATEWAY_URL}/me/keys`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
    if (!res.ok) throw new Error((await res.json()).detail || "Failed to load keys")
    return res.json() as Promise<{ items: ApiKey[] }>
  }

  async userUsage(accessToken: string) {
    const res = await fetch(`${GATEWAY_URL}/me/usage`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
    if (!res.ok) throw new Error((await res.json()).detail || "Failed to load usage")
    return res.json() as Promise<{ items: Array<{ key_id: string; request_count: number; total_tokens: number }> }>
  }

  // API Keys
  async getKeys(params?: {
    page?: number
    page_size?: number
    sort_by?: string
    sort_dir?: SortDir
    status?: "active" | "revoked"
    q?: string
    expired?: boolean
    has_expiration?: boolean
  }): Promise<Paginated<ApiKey>> {
    const search = new URLSearchParams()
    if (params?.page) search.set("page", String(params.page))
    if (params?.page_size) search.set("page_size", String(params.page_size))
    if (params?.sort_by) search.set("sort_by", params.sort_by)
    if (params?.sort_dir) search.set("sort_dir", params.sort_dir)
    if (params?.status) search.set("status", params.status)
    if (params?.q) search.set("q", params.q)
    if (params?.expired !== undefined) search.set("expired", String(params.expired))
    if (params?.has_expiration !== undefined) search.set("has_expiration", String(params.has_expiration))
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

  // Organizations
  async getOrganizations(): Promise<{ items: Organization[] }> {
    return this.request("/admin/organizations")
  }

  async createOrganization(data: { name: string; status?: string; monthly_token_quota?: number | null }): Promise<Organization> {
    return this.request("/admin/organizations", { method: 'POST', body: JSON.stringify(data) })
  }

  async updateOrganization(id: string, data: { name?: string; status?: string; monthly_token_quota?: number | null }): Promise<Organization> {
    return this.request(`/admin/organizations/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
  }

  async deleteOrganization(id: string): Promise<{ ok: boolean }> {
    return this.request(`/admin/organizations/${id}`, { method: 'DELETE' })
  }

  // Teams
  async getTeams(params?: { organization_id?: string }): Promise<{ items: Team[] }> {
    const qs = params?.organization_id ? `?organization_id=${encodeURIComponent(params.organization_id)}` : ''
    return this.request(`/admin/teams${qs}`)
  }

  async createTeam(data: { organization_id: string; name: string; description?: string | null }): Promise<Team> {
    return this.request('/admin/teams', { method: 'POST', body: JSON.stringify(data) })
    }

  async updateTeam(id: string, data: { name?: string; description?: string | null }): Promise<Team> {
    return this.request(`/admin/teams/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
  }

  async deleteTeam(id: string): Promise<{ ok: boolean }> {
    return this.request(`/admin/teams/${id}`, { method: 'DELETE' })
  }

  // Memberships
  async getMemberships(params?: { team_id?: string; user_id?: string }): Promise<{ items: Membership[] }> {
    const search = new URLSearchParams()
    if (params?.team_id) search.set('team_id', params.team_id)
    if (params?.user_id) search.set('user_id', params.user_id)
    const qs = search.toString()
    return this.request(`/admin/memberships${qs ? `?${qs}` : ''}`)
  }

  async addMembership(data: { team_id: string; user_id: string; role?: string }): Promise<Membership> {
    return this.request('/admin/memberships', { method: 'POST', body: JSON.stringify(data) })
  }

  async removeMembership(id: string): Promise<{ ok: boolean }> {
    return this.request(`/admin/memberships/${id}`, { method: 'DELETE' })
  }
}

export const apiClient = new ApiClient()
