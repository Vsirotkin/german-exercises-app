import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), vueDevTools(), tailwindcss()],

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },

  server: {
    proxy: {
      // Django Admin: только пути /admin/, не /admin-dashboard.
      '/static/': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/admin/': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/recommendations': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/results': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})
