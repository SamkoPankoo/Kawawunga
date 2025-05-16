// src/stores/auth.js - Original with minimal changes
import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import authService from '../services/auth'
import router from '../router'

export const useAuthStore = defineStore('auth', () => {
    const user = ref(null)
    const token = ref(localStorage.getItem('token') || null)
    const lastTokenRefresh = ref(Date.now()) // Track last token refresh

    const isAuthenticated = computed(() => !!token.value)
    const isAdmin = computed(() => user.value?.role === 'admin')

    // Watch for changes to token and save to localStorage
    watch(token, (newToken) => {
        if (newToken) {
            localStorage.setItem('token', newToken)
            console.log('Token saved to localStorage')
            // Update refresh timestamp
            lastTokenRefresh.value = Date.now()
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
            console.log('Login successful, token set:', token.value ? 'yes' : 'no')
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

        // Check if token refresh is needed - if it's been more than 5 minutes
        const tokenAge = Date.now() - lastTokenRefresh.value
        console.log(`Token age: ${tokenAge/1000} seconds`)

        try {
            console.log('Fetching current user data...')
            const response = await authService.getCurrentUser()
            user.value = response.data
            console.log('User fetched successfully:', user.value?.email)

            // Update token refresh timestamp
            lastTokenRefresh.value = Date.now()

            return response.data
        } catch (error) {
            console.error('Failed to fetch user:', error)

            // Only clear auth state for 401 errors (unauthorized)
            if (error.response?.status === 401) {
                console.warn('Token is invalid or expired, clearing auth state')
                user.value = null
                token.value = null
                localStorage.removeItem('token')
            }

            return null
        }
    }

    // Check token validity
    async function checkTokenValidity() {
        if (!token.value) return false

        try {
            // Use a lightweight endpoint to verify token validity
            await authService.getCurrentUser()
            return true
        } catch (error) {
            if (error.response?.status === 401) {
                // Token is invalid - clear auth state
                console.warn('Token validation failed, clearing auth state')
                user.value = null
                token.value = null
                localStorage.removeItem('token')
                return false
            }
            // For other errors, assume token might still be valid
            console.error('Error checking token validity:', error)
            return true
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
        fetchUser,
        checkTokenValidity
    }
})