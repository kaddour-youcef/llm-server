import { create } from "zustand"
import { persist } from "zustand/middleware"
import { apiClient } from "./api"

interface UserAuthState {
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isBusy: boolean
  login: (email: string, password: string) => Promise<boolean>
  register: (name: string, email: string, password: string) => Promise<boolean>
  refresh: () => Promise<boolean>
  logout: () => void
}

export const useUserAuthStore = create<UserAuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isBusy: false,

      async login(email, password) {
        set({ isBusy: true })
        try {
          const res = await apiClient.userLogin({ email, password })
          set({ accessToken: res.access_token, refreshToken: res.refresh_token, isAuthenticated: true, isBusy: false })
          return true
        } catch {
          set({ isBusy: false, accessToken: null, refreshToken: null, isAuthenticated: false })
          return false
        }
      },

      async register(name, email, password) {
        set({ isBusy: true })
        try {
          await apiClient.userRegister({ name, email, password })
          set({ isBusy: false })
          return true
        } catch {
          set({ isBusy: false })
          return false
        }
      },

      async refresh() {
        const { refreshToken } = get()
        if (!refreshToken) return false
        try {
          const res = await apiClient.userRefresh(refreshToken)
          set({ accessToken: res.access_token, isAuthenticated: true })
          return true
        } catch {
          set({ accessToken: null, isAuthenticated: false })
          return false
        }
      },

      logout() {
        set({ accessToken: null, refreshToken: null, isAuthenticated: false })
      },
    }),
    {
      name: "user-auth",
      partialize: (s) => ({ accessToken: s.accessToken, refreshToken: s.refreshToken }),
    },
  ),
)

