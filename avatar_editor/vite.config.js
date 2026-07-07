import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import electron from 'vite-plugin-electron'
import electronRenderer from 'vite-plugin-electron-renderer'
import fs from 'node:fs'
import path from 'node:path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    electron({
      entry: 'electron/main.js',
    }),
    electronRenderer(),
    {
      name: 'copy-preload',
      buildStart() {
        const src = path.resolve('electron/preload.cjs')
        const dest = path.resolve('dist-electron/preload.cjs')
        const dir = path.dirname(dest)
        if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
        fs.copyFileSync(src, dest)
      },
    },
  ],
})
