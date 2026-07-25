import { defineStore } from 'pinia'

import {
  getCurrentUser,
  loginUser,
  registerUser,
  type LoginPayload,
  type RegisterPayload,
  type User,
} from '../api/auth'
import {
  clearAuthToken,
  getAuthToken,
  saveAuthToken,
} from '../utils/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    token: getAuthToken(),
    initialized: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token && state.user),
  },
  actions: {
    async initialize(): Promise<void> {
      if (this.initialized) return

      if (this.token) {
        try {
          this.user = await getCurrentUser()
        } catch {
          this.logout()
        }
      }
      this.initialized = true
    },
    async login(payload: LoginPayload): Promise<void> {
      const response = await loginUser(payload)
      this.token = response.access_token
      saveAuthToken(response.access_token)
      try {
        this.user = await getCurrentUser()
        this.initialized = true
      } catch (error) {
        this.logout()
        throw error
      }
    },
    async register(payload: RegisterPayload): Promise<void> {
      await registerUser(payload)
      await this.login({
        identity: payload.email,
        password: payload.password,
      })
    },
    logout(): void {
      clearAuthToken()
      this.token = null
      this.user = null
      this.initialized = true
    },
  },
})
