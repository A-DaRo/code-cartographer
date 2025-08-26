/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // --- ADD THIS ENTIRE 'server' SECTION ---
  server: {
    proxy: {
      // Any request that starts with '/api' will be proxied
      '/api': {
        // The target is your Python backend server
        target: 'http://127.0.0.1:8000',
        // This is needed for the backend to correctly process the request
        changeOrigin: true,
      },
    },
  },
  // ------------------------------------------
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test-setup.ts',
  },
});