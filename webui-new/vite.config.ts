import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',  // Allow external access
    port: 5173,       // Specify exact port
    strictPort: true, // Fail if port is already in use
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  build: {
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html'),
        playground: path.resolve(__dirname, 'playground.html'),
        createPipeline: path.resolve(__dirname, 'create-pipeline.html'),
        // Include these entries only if they exist
        pg: path.resolve(__dirname, 'pg.html'),
        cpl: path.resolve(__dirname, 'cpl.html'),
      }
    }
  }
});