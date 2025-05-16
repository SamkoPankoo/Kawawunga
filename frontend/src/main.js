// src/main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import i18n from './plugins/i18n'
import { setupInterceptors } from './services/api'
import './assets/styles/main.css'

// Create the app and install plugins
const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
window.$pinia = pinia;
// Import auth store after pinia is installed
import { useAuthStore } from './stores/auth'

const customTheme = {
    dark: false,
    colors: {
        primary: '#E53935', // Red primary color
        secondary: '#FF5252', // Lighter red for secondary
        accent: '#FF8A80', // Even lighter red for accents
        // Keep other colors as needed
    },
}

// Install other plugins
app.use(router)
app.use(vuetify, {
    theme: customTheme
})
app.use(i18n)

// Get auth store instance and set up API interceptors
const authStore = useAuthStore()
setupInterceptors(authStore)

// Try to fetch user data if token exists - but with better error handling
if (authStore.token) {
    console.log('Found existing token, trying to restore session...')
    authStore.fetchUser()
        .then(userData => {
            if (userData) {
                console.log('User session restored successfully:', userData.email)
            } else {
                console.warn('Could not restore user session, token may be invalid')
            }
        })
        .catch(err => {
            console.error('Failed to restore session:', err.message)
            // Don't logout here, as fetchUser already handles invalid tokens
        })
}

// Mount the app
app.mount('#app')