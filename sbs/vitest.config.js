import { defineConfig } from 'vitest/config';

// Standalone Vitest config to avoid loading SvelteKit vite plugin for unit tests.
export default defineConfig({
  test: {
    environment: 'node',
    include: ['src/**/*.test.js'],
    pool: 'forks',
    singleThread: true
  },
  plugins: []
});
