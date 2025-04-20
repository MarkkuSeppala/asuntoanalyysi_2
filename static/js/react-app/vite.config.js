import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // Output to Flask's static directory
    outDir: '../../../static/dist',
    emptyOutDir: true,
    sourcemap: true,
  },
  server: {
    proxy: {
      '/api': 'http://localhost:5000',
      '/auth': 'http://localhost:5000',
      '/analyses': 'http://localhost:5000',
      '/analyze': 'http://localhost:5000'
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
}); 