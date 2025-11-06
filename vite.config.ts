import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
      manifest: {
        name: 'CogniForge - AI-Powered Educational Platform',
        short_name: 'CogniForge',
        description: 'Advanced AI-powered educational platform with cutting-edge UI/UX',
        theme_color: '#4fc3f7',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    })
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './app/static/src'),
      '@components': path.resolve(__dirname, './app/static/src/components'),
      '@utils': path.resolve(__dirname, './app/static/src/utils'),
      '@hooks': path.resolve(__dirname, './app/static/src/hooks'),
      '@types': path.resolve(__dirname, './app/static/src/types')
    }
  },
  build: {
    outDir: 'app/static/dist',
    assetsDir: 'assets',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'three-vendor': ['three', '@react-three/fiber', '@react-three/drei'],
          'chart-vendor': ['d3', 'recharts', 'plotly.js', 'chart.js'],
          'ai-vendor': ['@tensorflow/tfjs', 'tone'],
          'editor-vendor': ['monaco-editor', '@monaco-editor/react']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/admin': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})
