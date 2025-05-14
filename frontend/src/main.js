import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import i18n from './plugins/i18n'
import { setupInterceptors } from './services/api'
import './assets/styles/main.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)

// Import auth store after pinia is installed
import { useAuthStore } from './stores/auth'

// Create the app and install plugins
app.use(router)
app.use(vuetify)
app.use(i18n)

// Mount the app
app.mount('#app')

// Set up API interceptors after auth store is available
const authStore = useAuthStore()
setupInterceptors(authStore)

// Try to fetch user data if token exists
if (authStore.token) {
    authStore.fetchUser()
        .then(() => console.log('User data loaded successfully'))
        .catch(err => console.error('Failed to load user data:', err))
}