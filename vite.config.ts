// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

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
          { src: 'pwa-192x192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png' }
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
      '@types': path.resolve(__dirname, './app/static/src/types'),

      // ✳️ هذا هو المهم:
      // عندما يطلب react-plotly.js -> "plotly.js/dist/plotly"
      // نعطيه الملف الحقيقي المصغّر:
      'plotly.js/dist/plotly': path.resolve(
        __dirname,
        'node_modules/plotly.js-dist-min/plotly.min.js'
      )
    }
  },

  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version || 'dev')
  },

  server: {
    port: 5173,
    strictPort: false,
    host: true,
    open: false,
    proxy: {
      '/api':   { target: 'http://localhost:5001', changeOrigin: true },
      '/admin': { target: 'http://localhost:5001', changeOrigin: true }
    }
  },

  preview: {
    port: 5180,
    proxy: {
      '/api':   { target: 'http://localhost:5001', changeOrigin: true },
      '/admin': { target: 'http://localhost:5001', changeOrigin: true }
    }
  },

  build: {
    target: 'es2020',
    outDir: 'app/static/dist',
    assetsDir: 'assets',
    sourcemap: true,
    chunkSizeWarningLimit: 700,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'three-vendor': ['three', '@react-three/fiber', '@react-three/drei'],
          // لا تضع اسم الحزمة المصغّرة هنا؛ alias يوجه الملف تلقائيًا
          'chart-vendor': ['recharts', 'react-plotly.js', 'chart.js'],
          'ai-vendor': ['@tensorflow/tfjs', 'tone'],
          'editor-vendor': ['monaco-editor', '@monaco-editor/react']
        }
      }
    }
  },

  optimizeDeps: {
    // لا تدرج plotly.js-dist-min هنا؛ دع alias يتكفل بالمسار
    include: ['react', 'react-dom', 'react-plotly.js', 'recharts'],
    exclude: ['monaco-editor']
  }
})
