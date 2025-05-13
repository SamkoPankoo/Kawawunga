// Create a vite.config.js file in your frontend directory if it doesn't exist:
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import vuetify from 'vite-plugin-vuetify';

export default defineConfig({
  plugins: [
    vue(),
    vuetify({ autoImport: true })
  ],
  resolve: {
    alias: {
      // Add any aliases you need
    }
  },
  server: {
    host: true,
    port: 8080
  },
  define: {
    // This helps with libraries that use process.env
    'process.env': {},
    // Some libraries check for process directly
    'process': {
      env: {}
    }
  }
});