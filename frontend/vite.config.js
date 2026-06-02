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
            // 后端 FastAPI 路由本身就挂在 /api/v1/... 下，这里**不要**重写路径
            '/api': {
                target: 'http://127.0.0.1:8000/',
                changeOrigin: true,
                ws: true  // 让 /api/v1/agent/ws 也走这个代理
            },
            // MCP SSE（FastAPI-MCP 挂在 /mcp）
            '/mcp': {
                target: 'http://127.0.0.1:8000/',
                changeOrigin: true
            }
        }
    }
})
