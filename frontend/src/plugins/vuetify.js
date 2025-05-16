// frontend/src/plugins/vuetify.js
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'

export default createVuetify({
    components,
    directives,
    theme: {
        defaultTheme: 'light',
        themes: {
            light: {
                colors: {
                    primary: '#E53935', // Red primary color
                    secondary: '#FF5252', // Lighter red for secondary
                    accent: '#FF8A80', // Light red accent
                    error: '#B71C1C', // Dark red for errors
                    info: '#2196F3', // Keep blue for info
                    success: '#4CAF50', // Keep green for success
                    warning: '#FFC107', // Keep amber for warnings
                }
            }
        }
    }
})