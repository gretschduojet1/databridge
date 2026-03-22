import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig({
  plugins: [svelte()],
  server: {
    host: '0.0.0.0',  // required to be reachable outside the Docker container
    port: 5173,
  },
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      include: ['src/lib/**'],
      reporter: ['text', 'lcov', 'cobertura'],
      thresholds: { lines: 80 },
    },
  },
})
