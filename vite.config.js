import { defineConfig } from 'vite'
import { resolve } from 'path'
import { copyFileSync, existsSync } from 'fs'
import tailwindcss from 'tailwindcss'
import autoprefixer from 'autoprefixer'

// Plugin to copy plotly.min.js after each build (including watch rebuilds)
function copyPlotly() {
  return {
    name: 'copy-plotly',
    closeBundle() {
      const src = resolve(__dirname, 'node_modules/plotly.js-dist-min/plotly.min.js')
      const dest = resolve(__dirname, 'app/static/build/plotly.min.js')
      if (existsSync(src)) {
        copyFileSync(src, dest)
        console.log('✓ Copied plotly.min.js to build/')
      }
    }
  }
}

export default defineConfig({
  root: 'app/static',
  base: '/static/build/',
  plugins: [copyPlotly()],

  build: {
    outDir: 'build',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        vendor: resolve(__dirname, 'app/static/js/vendor.js'),
        htmx: resolve(__dirname, 'app/static/js/htmx.js'),
        map: resolve(__dirname, 'app/static/js/map.js'),
        'report-form': resolve(__dirname, 'app/static/js/report-form-htmx.js'),
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
