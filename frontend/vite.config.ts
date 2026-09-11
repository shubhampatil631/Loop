import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/onboarding': 'http://127.0.0.1:8000',
      '/session': 'http://127.0.0.1:8000',
      '/review': 'http://127.0.0.1:8000',
      '/progress': 'http://127.0.0.1:8000',
      '/users': 'http://127.0.0.1:8000',
      '/mcp': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000'
    }
  }
})

