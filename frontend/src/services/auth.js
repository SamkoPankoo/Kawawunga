// src/services/auth.js
import api from './api'

export default {
    login(credentials) {
        return api.post('/auth/login', credentials)
            .catch(error => {
                console.error('Login failed:', error);
                throw error;
            });
    },

    register(userData) {
        return api.post('/auth/register', userData)
            .catch(error => {
                console.error('Registration failed:', error);
                throw error;
            });
    },

    getCurrentUser() {
        return api.get('/auth/me')
            .catch(error => {
                console.error('Failed to fetch current user:', error);
                throw error;
            });
    },

    checkServerStatus() {
        return api.get('/health')
            .then(() => ({ status: 'online' }))
            .catch(error => {
                console.error('Server health check failed:', error);
                return { status: 'offline', error };
            });
    },

    // Additional helper method to verify token without fetching full user data
    verifyToken(token) {
        return api.get('/auth/verify', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        }).catch(error => {
            console.error('Token verification failed:', error);
            throw error;
        });
    }
}