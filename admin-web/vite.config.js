import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Nhận request từ ngrok và các thiết bị khác trong mạng.
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    allowedHosts: ['zero-haven-disparate.ngrok-free.dev'],
    // Giữ backend ở máy local; request đi qua cùng host ngrok với giao diện.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/audio': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
