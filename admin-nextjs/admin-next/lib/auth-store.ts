import { create } from "zustand"
import { persist } from "zustand/middleware"
import { apiClient } from "./api"

interface AuthState {
  apiKey: string | null
  isAuthenticated: boolean
  isValidating: boolean
  setApiKey: (key: string) => void
  validateKey: () => Promise<boolean>
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      apiKey: null,
      isAuthenticated: false,
      isValidating: false,

      setApiKey: (key: string) => {
        set({ apiKey: key })
        apiClient.setApiKey(key)
      },

      validateKey: async () => {
        const { apiKey } = get()
        if (!apiKey) return false

        set({ isValidating: true })
        try {
          apiClient.setApiKey(apiKey)
          await apiClient.validateKey()
          set({ isAuthenticated: true, isValidating: false })
          return true
        } catch (error) {
          set({ isAuthenticated: false, isValidating: false, apiKey: null })
          return false
        }
      },

      logout: () => {
        set({ apiKey: null, isAuthenticated: false })
        apiClient.setApiKey("")
      },
    }),
    {
      name: "admin-auth",
      partialize: (state) => ({ apiKey: state.apiKey }),
    },
  ),
)
