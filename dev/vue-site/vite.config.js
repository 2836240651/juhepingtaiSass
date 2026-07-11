import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
  base: env.VITE_BASE_PATH || '/',
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: true,
    port: 5173,
    strictPort: false,
    proxy: {
      '/api/temu': {
        target: process.env.VITE_TEMU_API_PROXY || 'http://localhost:18080',
        changeOrigin: true,
      },
      '/api/auth': {
        target: process.env.VITE_TEMU_API_PROXY || 'http://localhost:18080',
        changeOrigin: true,
      },
      '/api/warehouse': {
        target: process.env.VITE_TEMU_API_PROXY || 'http://localhost:18080',
        changeOrigin: true,
      },
      '/api/tenant': {
        target: process.env.VITE_TEMU_API_PROXY || 'http://localhost:18080',
        changeOrigin: true,
      },
      '/api/platform-accounts': {
        target: process.env.VITE_TEMU_API_PROXY || 'http://localhost:18080',
        changeOrigin: true,
      },
      '/api/aliexpress': {
        target: process.env.VITE_TEMU_API_PROXY || 'http://localhost:18080',
        changeOrigin: true,
      },
      '/api/monitor': {
        target: process.env.VITE_TEMU_API_PROXY || 'http://localhost:18080',
        changeOrigin: true,
      },
      '/api/tasks': {
        target: process.env.VITE_TEMU_API_PROXY || 'http://localhost:18080',
        changeOrigin: true,
      },
      '/api/ops-feedback': {
        target: process.env.VITE_TEMU_API_PROXY || 'http://localhost:18080',
        changeOrigin: true,
      },
      '/api/amazon': {
        target: process.env.VITE_TEMU_API_PROXY || 'http://localhost:18080',
        changeOrigin: true,
      },
      '/api/agent': {
        target: process.env.VITE_TEMU_API_PROXY || 'http://localhost:18080',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: true,
    port: 4173,
  },
}})
