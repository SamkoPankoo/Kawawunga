import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import authService from '../services/auth'
import router from '../router'

export const useAuthStore = defineStore('auth', () => {
    const user = ref(null)
    const token = ref(localStorage.getItem('token') || null)

    const isAuthenticated = computed(() => !!token.value)
    const isAdmin = computed(() => user.value?.role === 'admin')

    // Watch for changes to token and save to localStorage
    watch(token, (newToken) => {
        if (newToken) {
            localStorage.setItem('token', newToken)
            console.log('Token saved to localStorage')
        } else {
            localStorage.removeItem('token')
            console.log('Token removed from localStorage')
        }
    })

    async function login(credentials) {
        try {
            const response = await authService.login(credentials)
            token.value = response.data.token
            user.value = response.data.user
            console.log('Login successful, token set:', !!token.value)
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

    async function logout() {
        user.value = null;
        token.value = null;
        localStorage.removeItem('token');
        console.log('Logout complete, auth state cleared');

        // Force redirect to login page on logout
        router.push('/login');
    }

    async function fetchUser() {
        if (!token.value) {
            console.warn('Cannot fetch user: No token')
            return null
        }

        try {
            const response = await authService.getCurrentUser()
            user.value = response.data
            console.log('User fetched successfully:', user.value?.email)
            return response.data
        } catch (error) {
            console.error('Failed to fetch user:', error)
            // If fetch user fails, clear state
            token.value = null
            user.value = null
            localStorage.removeItem('token')
            return null
        }
    }

    // Initialize - fetch user if token exists
    if (token.value) {
        console.log('Token found, fetching user...')
        fetchUser()
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