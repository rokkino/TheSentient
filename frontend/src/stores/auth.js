import { defineStore } from 'pinia'
import api from '../services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: null,
    isAuthenticated: false,
  }),

  getters: {
    // Computed getters for backward compatibility
    currentUser: (state) => state.user,
    isLoggedIn: (state) => state.isAuthenticated,
  },

  actions: {
    async login(username, password) {
      try {
        const response = await api.login(username, password)
        this.token = response.data.access_token
        this.isAuthenticated = true
        localStorage.setItem('token', this.token)
        
        // Get user info
        await this.fetchUser()
        return { success: true }
      } catch (error) {
        return { 
          success: false, 
          error: error.response?.data?.detail || 'Login failed' 
        }
      }
    },

    async register(username, email, password) {
      try {
        const response = await api.register(username, email, password)
        console.log('Registration response:', response.data)
        // Auto-login after registration
        const loginResult = await this.login(username, password)
        if (loginResult.success) {
          return { success: true }
        } else {
          return { 
            success: false, 
            error: loginResult.error || 'Registration successful but login failed. Please try logging in manually.' 
          }
        }
      } catch (error) {
        console.error('Registration error:', error)
        const errorMessage = error.response?.data?.detail || error.message || 'Registration failed'
        return { 
          success: false, 
          error: errorMessage
        }
      }
    },

    async logout() {
      try {
        await api.logout()
      } catch (error) {
        console.error('Logout error:', error)
      } finally {
        this.user = null
        this.token = null
        this.isAuthenticated = false
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      }
    },

    async fetchUser() {
      try {
        const response = await api.getCurrentUser()
        this.user = response.data
        localStorage.setItem('user', JSON.stringify(this.user))
        return this.user
      } catch (error) {
        console.error('Failed to fetch user:', error)
        // If token is invalid, logout
        if (error.response?.status === 401) {
          this.logout()
        }
        return null
      }
    },

    async updateProfile(profileData) {
      try {
        const response = await api.updateProfile(profileData)
        this.user = { ...this.user, ...response.data }
        localStorage.setItem('user', JSON.stringify(this.user))
        return { success: true }
      } catch (error) {
        return { 
          success: false, 
          error: error.response?.data?.detail || 'Failed to update profile' 
        }
      }
    },

    async checkAuth() {
      const token = localStorage.getItem('token')
      if (token) {
        this.token = token
        this.isAuthenticated = true
        await this.fetchUser()
      }
    },
  },
})

