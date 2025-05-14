// src/services/api.js
import axios from 'axios';

// Get base URL from environment variable or use relative path
const baseURL = import.meta.env.VITE_API_URL || '/kawawunga/api';

// Create API instance
const api = axios.create({
    baseURL,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Add a method to get auth headers based on token or API key
export const getAuthHeaders = (token, apiKey) => {
    const headers = {};

    // Add token if available
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Add API key if available
    if (apiKey) {
        headers['X-API-Key'] = apiKey;
    }

    return headers;
};

// Add request interceptor that will be called after auth store is available
export const setupInterceptors = (authStore) => {
    api.interceptors.request.use(config => {
        if (!config.headers) {
            config.headers = {};
        }

        // Add token for authenticated requests
        if (authStore.token) {
            config.headers.Authorization = `Bearer ${authStore.token}`;
        }

        // Add API key for specific routes
        if (config.url.includes('/history') ||
            config.url.includes('/users') ||
            config.url.includes('/pdfLogs')) {
            if (authStore.user?.apiKey) {
                config.headers['X-API-Key'] = authStore.user.apiKey;
            } else {
                console.warn(`No API key available for request to ${config.url}`);
            }
        }

        return config;
    });

    // Add response interceptor
    api.interceptors.response.use(
        response => response,
        error => {
            if (error.response?.status === 401) {
                console.error(`Unauthorized request to ${error.config?.url} - auth info might be missing or invalid`);
                console.log("Auth status:", {
                    token: authStore.token ? "Present" : "Missing",
                    apiKey: authStore.user?.apiKey ? "Present" : "Missing",
                    headers: error.config?.headers
                });
            }
            return Promise.reject(error);
        }
    );
};

export default api;