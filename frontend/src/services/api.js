import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    headers: {
        'Content-Type': 'application/json'
    }
})

api.interceptors.request.use(config => {
    const authStore = useAuthStore()
    if (authStore.token) {
        config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
})

api.interceptors.response.use(
    response => response,
    async error => {
        const originalRequest = error.config;

        // If error is network error and we haven't retried yet
        if ((error.message === 'Network Error' || error.code === 'ERR_NETWORK')
            && !originalRequest._retry
            && originalRequest.method.toLowerCase() === 'post') {
            originalRequest._retry = true;
            console.log('Network error, retrying in 2 seconds...');

            // Wait 2 seconds before retrying
            await new Promise(resolve => setTimeout(resolve, 2000));
            return api(originalRequest);
        }

        if (error.response?.status === 401) {
            const authStore = useAuthStore();
            authStore.logout();
        }

        return Promise.reject(error);
    }
);

export default api