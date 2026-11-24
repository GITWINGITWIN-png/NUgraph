import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The dev server proxies /api -> the FastAPI backend on :8001
// (8000 is taken by another project), so the frontend never deals with CORS.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5180, // 5173/5174 are used by other local projects
    proxy: {
      '/api': 'http://localhost:8001',
    },
  },
})
