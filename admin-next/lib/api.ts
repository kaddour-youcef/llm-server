// Prefer browser-exposed env; fall back for dev
const GATEWAY_URL =
  process.env.NEXT_PUBLIC_GATEWAY_URL ||
  process.env.GATEWAY_URL ||
  "http://localhost:8080"

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
      const error = await response.text()
      throw new Error(error || `HTTP ${response.status}`)
    }

    return response.json()
  }

  // Auth validation
  async validateKey() {
    return this.request("/admin/users")
  }

  // Users
  async getUsers(params?: { page?: number; page_size?: number }) {
    const search = new URLSearchParams()
    if (params?.page) search.set("page", String(params.page))
    if (params?.page_size) search.set("page_size", String(params.page_size))
    const qs = search.toString()
    return this.request(`/admin/users${qs ? `?${qs}` : ""}`)
  }

  async createUser(data: { name: string; email?: string }) {
    return this.request("/admin/users", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  // API Keys
  async getKeys(params?: { page?: number; page_size?: number }) {
    const search = new URLSearchParams()
    if (params?.page) search.set("page", String(params.page))
    if (params?.page_size) search.set("page_size", String(params.page_size))
    const qs = search.toString()
    return this.request(`/admin/keys${qs ? `?${qs}` : ""}`)
  }

  async createKey(data: {
    user_id: string
    name: string
    role: string
    monthly_quota_tokens?: number | null
    daily_request_quota?: number | null
  }) {
    return this.request("/admin/keys", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async revokeKey(keyId: string) {
    return this.request(`/admin/keys/${keyId}/revoke`, {
      method: "POST",
    })
  }

  async rotateKey(keyId: string) {
    return this.request(`/admin/keys/${keyId}/rotate`, {
      method: "POST",
    })
  }

  // Usage
  async getUsage(params: { from: string; to: string; key_id?: string }) {
    const searchParams = new URLSearchParams(params)
    return this.request(`/admin/usage?${searchParams}`)
  }

  // Requests
  async getRequests() {
    return this.request("/admin/requests")
  }
}

export const apiClient = new ApiClient()
