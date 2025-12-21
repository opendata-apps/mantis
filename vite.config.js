import { defineConfig } from 'vite'
import { resolve } from 'path'
import tailwindcss from 'tailwindcss'
import autoprefixer from 'autoprefixer'

export default defineConfig({
  root: 'app/static',
  base: '/static/build/',

  build: {
    outDir: 'build',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        vendor: resolve(__dirname, 'app/static/js/vendor.js'),
        map: resolve(__dirname, 'app/static/js/map.js'),
        'report-form': resolve(__dirname, 'app/static/js/report-form.js'),
        gallery: resolve(__dirname, 'app/static/js/gallery.js'),
        confetti: resolve(__dirname, 'app/static/js/confetti.js'),
        theme: resolve(__dirname, 'app/static/css/theme.css'),
      },
      output: {
        entryFileNames: '[name]-[hash].js',
        chunkFileNames: '[name]-[hash].js',
        assetFileNames: '[name]-[hash][extname]',
      },
    },
  },

  css: {
    postcss: {
      plugins: [tailwindcss, autoprefixer],
    },
  },

  server: {
    origin: 'http://localhost:5173',
    port: 5173,
    strictPort: true,
  },
})
