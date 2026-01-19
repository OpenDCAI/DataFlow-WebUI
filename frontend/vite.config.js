import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
    base: './',
    plugins: [
        vue(),
    ],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url))
        }
    },
    css: {
        preprocessorOptions: {
            scss: {
                additionalData: `@use "@/style/global.scss" as *;`
            }
        }
    },
    server: {
        proxy: {
            '/api': {
                target: 'http://100.64.0.91:8000/', // 后端 FastAPI 地址
                changeOrigin: true,
                rewrite: path => path.replace(/^\/api/, '') // 如果后端没有 /api 前缀
            }
        }
    }
})
