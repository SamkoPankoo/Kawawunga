import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import authService from '../services/auth'

export const useAuthStore = defineStore('auth', () => {
    const user = ref(null)
    const token = ref(localStorage.getItem('token'))

    const isAuthenticated = computed(() => !!token.value)
    const isAdmin = computed(() => user.value?.role === 'admin')

    async function login(credentials) {
        try {
            const response = await authService.login(credentials)
            token.value = response.data.token
            user.value = response.data.user
            localStorage.setItem('token', token.value)
            return true
        } catch (error) {
            console.error('Login failed:', error)
            throw error
        }
    }

    async function register(userData) {
        try {
            const response = await authService.register(userData)
            return response.data
        } catch (error) {
            console.error('Registration failed:', error)
            throw error
        }
    }

    function logout() {
        user.value = null
        token.value = null
        localStorage.removeItem('token')
    }

    async function fetchUser() {
        if (!token.value) return

        try {
            const response = await authService.getCurrentUser()
            user.value = response.data
        } catch (error) {
            console.error('Failed to fetch user:', error)
            logout()
        }
    }

    return {
        user,
        token,
        isAuthenticated,
        isAdmin,
        login,
        register,
        logout,
        fetchUser
    }
})
//frontend/src/stores/auth.js