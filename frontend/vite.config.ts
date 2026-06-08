import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// Single-Container: FastAPI liefert das gebaute dist/ aus.
// Im Dev (npm run dev) werden /api, /icons, /health ans Backend (8766) geproxyt.
export default defineConfig({
  plugins: [svelte()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8766',
      '/icons': 'http://localhost:8766',
      '/health': 'http://localhost:8766',
    },
  },
})
