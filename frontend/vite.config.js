// vite.config.js
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import vuetify from 'vite-plugin-vuetify';
import path from 'path';

export default defineConfig({
  plugins: [
    vue(),
    vuetify({ autoImport: true })
  ],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    }
  },
  server: {
    host: true,
    port: 8080,
    proxy: {
      // Proxy pre backend API
      '/api': {
        target: 'http://backend:3000',
        changeOrigin: true
      },
      // Proxy pre Python službu
      '/python-api': {
        target: 'http://python-service:5000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/python-api/, '')
      }
    }
  },
  define: {
    'process.env': {},
    'process': {
      env: {}
    }
  }
});